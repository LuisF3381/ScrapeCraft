import argparse
import logging
import pandas as pd
import yaml
from datetime import datetime
from pathlib import Path
from src.shared.driver_config import DriverConfig
from src.shared.logger import setup_logger
from src.shared.storage import save_data, save_raw, cleanup_raw, load_raw
from src.viviendas_adonde.scraper import scrape
from src.viviendas_adonde.process import process
from config import global_settings
from config.viviendas_adonde import settings

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
#   Este archivo no requiere modificaciones.
# ---------------------------------------------------------------------------

# Se deriva automaticamente del nombre de la carpeta del job (no modificar)
_JOB_NAME = Path(__file__).parent.name
WEB_CONFIG_PATH = Path(__file__).parent.parent.parent / "config" / _JOB_NAME / "web_config.yaml"


def load_web_config() -> dict:
    """Carga la configuracion de la web desde el archivo YAML."""
    with open(WEB_CONFIG_PATH, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    logger.info(f"Configuracion cargada: {config['url']}")
    return config


# ---------------------------------------------------------------------------
# Flujos internos (no modificar)
# ---------------------------------------------------------------------------

def _run_full() -> list[dict]:
    """Flujo completo: scraping → raw → (proceso opcional) → limpieza de raw."""
    logger.info("Iniciando scraper...")

    web_config = load_web_config()
    driver = DriverConfig(**settings.DRIVER_CONFIG).get_driver()

    try:
        datos = scrape(driver, web_config)
    finally:
        driver.quit()

    if not datos:
        raise RuntimeError("El scraper no retorno datos. Verifica la URL, los selectores o posible bloqueo.")

    suffix: str = save_raw(datos, settings.RAW_CONFIG, global_settings.DATA_CONFIG)
    del datos

    skip_process: bool = settings.PIPELINE_CONFIG.get("skip_process", False)

    if skip_process:
        logger.info("skip_process=True: omitiendo process.py, usando raw directamente")
        processed = load_raw(
            filename=settings.RAW_CONFIG["filename"],
            extension=settings.RAW_CONFIG["format"],
            suffix=suffix,
            raw_config=settings.RAW_CONFIG,
            data_config=global_settings.DATA_CONFIG,
        )
    else:
        df = pd.DataFrame(load_raw(
            filename=settings.RAW_CONFIG["filename"],
            extension=settings.RAW_CONFIG["format"],
            suffix=suffix,
            raw_config=settings.RAW_CONFIG,
            data_config=global_settings.DATA_CONFIG,
        ))
        processed = process(df)

    cleanup_raw(settings.RAW_CONFIG)
    return processed


def _run_reprocess(suffix: str) -> list[dict]:
    """Flujo reprocess: omite el scraping y reprocesa un raw existente."""
    logger.info(f"Iniciando reprocesamiento: sufijo {suffix}")
    df = pd.DataFrame(load_raw(
        filename=settings.RAW_CONFIG["filename"],
        extension=settings.RAW_CONFIG["format"],
        suffix=suffix,
        raw_config=settings.RAW_CONFIG,
        data_config=global_settings.DATA_CONFIG,
    ))
    return process(df)


def _save_output(processed: list[dict]) -> None:
    """Guarda los datos procesados en todos los formatos configurados."""
    output_formats = settings.STORAGE_CONFIG.get("output_formats", ["csv"])
    now = datetime.now()
    for formato in output_formats:
        save_data(processed, formato, global_settings.DATA_CONFIG, settings.STORAGE_CONFIG, now)
    logger.info("Proceso finalizado")


# ---------------------------------------------------------------------------
# Punto de entrada del job (no modificar)
# ---------------------------------------------------------------------------

def run(args: argparse.Namespace) -> None:
    """
    Punto de entrada del job viviendas_adonde.

    Args:
        args.reprocess (str | None): sufijo del raw a reprocesar.
                                     Si es None se ejecuta el flujo completo.
    """
    setup_logger(_JOB_NAME, **global_settings.LOG_CONFIG)

    try:
        if args.reprocess:
            processed = _run_reprocess(args.reprocess)
        else:
            processed = _run_full()

        _save_output(processed)

    except Exception as e:
        logger.error(f"Error durante la ejecucion: {e}", exc_info=True)
        raise
