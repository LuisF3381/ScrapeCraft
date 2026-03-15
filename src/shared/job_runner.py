import argparse
import logging
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from src.shared.driver_config import DriverConfig
from src.shared.logger import setup_logger
from src.shared.storage import save_data, save_raw, cleanup_raw, load_raw
from config import global_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FLUJO ETL — vision general
#
#   FLUJO COMPLETO (skip_process=False):
#     run() → _run_full() → scrape()    → [scraper.py]   <- implementar aqui
#                         → save_raw()
#                         → process()   → [process.py]   <- implementar aqui
#                         → cleanup_raw()
#           → _save_output()
#
#   FLUJO SIN PROCESS (skip_process=True en PIPELINE_CONFIG):
#     run() → _run_full() → scrape()
#                         → save_raw()
#                         → load_raw()
#                         → cleanup_raw()
#           → _save_output()
#
#   FLUJO REPROCESS (--reprocess <sufijo>):
#     run() → _run_reprocess() → process()  → [process.py]
#           → _save_output()
#
#   Como data engineer solo debes implementar scraper.py y process.py.
#   app_job.py no requiere modificaciones: solo declara los imports del job.
# ---------------------------------------------------------------------------

_PROJECT_ROOT = Path(__file__).parent.parent.parent


def load_web_config(job_name: str) -> dict:
    """Carga la configuracion de la web desde el archivo YAML del job."""
    path = _PROJECT_ROOT / "config" / job_name / "web_config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logger.info(f"Configuracion cargada: {config['url']}")
    return config


# ---------------------------------------------------------------------------
# Flujos internos
# ---------------------------------------------------------------------------

def _run_full(scrape_fn, process_fn, settings, job_name: str, now: datetime) -> list[dict]:
    """Flujo completo: scraping → raw → (proceso opcional) → limpieza de raw."""
    logger.info("Iniciando scraper...")

    web_config = load_web_config(job_name)
    driver = DriverConfig(**settings.DRIVER_CONFIG).get_driver()

    try:
        datos = scrape_fn(driver, web_config)
    finally:
        driver.quit()

    if not datos:
        raise RuntimeError("El scraper no retorno datos. Verifica la URL, los selectores o posible bloqueo.")

    suffix: str = save_raw(datos, settings.RAW_CONFIG, global_settings.DATA_CONFIG, now)
    del datos

    raw_records: list[dict] = load_raw(
        filename=settings.RAW_CONFIG["filename"],
        extension=settings.RAW_CONFIG["format"],
        suffix=suffix,
        raw_config=settings.RAW_CONFIG,
        data_config=global_settings.DATA_CONFIG,
    )

    skip_process: bool = settings.PIPELINE_CONFIG.get("skip_process", False)

    if skip_process:
        logger.info("skip_process=True: omitiendo process.py, usando raw directamente")
        processed = raw_records
    else:
        processed = process_fn(pd.DataFrame(raw_records))

    cleanup_raw(settings.RAW_CONFIG)
    return processed


def _run_reprocess(suffix: str, process_fn, settings) -> list[dict]:
    """Flujo reprocess: omite el scraping y reprocesa un raw existente."""
    logger.info(f"Iniciando reprocesamiento: sufijo {suffix}")
    df = pd.DataFrame(load_raw(
        filename=settings.RAW_CONFIG["filename"],
        extension=settings.RAW_CONFIG["format"],
        suffix=suffix,
        raw_config=settings.RAW_CONFIG,
        data_config=global_settings.DATA_CONFIG,
    ))
    return process_fn(df)


def _save_output(processed: list[dict], settings, now: datetime) -> None:
    """Guarda los datos procesados en todos los formatos configurados."""
    output_formats = settings.STORAGE_CONFIG.get("output_formats", ["csv"])
    for formato in output_formats:
        save_data(processed, formato, global_settings.DATA_CONFIG, settings.STORAGE_CONFIG, now)
    logger.info("Proceso finalizado")


# ---------------------------------------------------------------------------
# Punto de entrada generico (llamado desde app_job.py de cada job)
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace, scrape_fn, process_fn, settings, job_name: str) -> None:
    """
    Punto de entrada generico para cualquier job.

    Args:
        args:       Argumentos CLI (args.reprocess: str | None)
        scrape_fn:  Funcion scrape() del job
        process_fn: Funcion process() del job
        settings:   Modulo de configuracion del job
        job_name:   Nombre del job (nombre de la carpeta en src/)
    """
    setup_logger(job_name, **global_settings.LOG_CONFIG)

    now = datetime.now()

    try:
        if args.reprocess:
            processed = _run_reprocess(args.reprocess, process_fn, settings)
        else:
            processed = _run_full(scrape_fn, process_fn, settings, job_name, now)

        _save_output(processed, settings, now)

    except Exception as e:
        logger.error(f"Error durante la ejecucion: {e}", exc_info=True)
        raise
