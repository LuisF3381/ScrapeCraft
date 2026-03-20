import argparse
import json
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

_LAST_PARAMS_FILENAME = "last_params.json"


def _parse_params(raw: str | None) -> dict:
    """
    Convierte el string de parametros CLI en un diccionario.

    Args:
        raw: String en formato "clave=valor&clave2=valor2", o None si no se paso --params

    Returns:
        dict con los parametros, o dict vacio si raw es None

    Raises:
        ValueError: Si algun par no tiene el formato "clave=valor"
    """
    if not raw:
        return {}
    try:
        return dict(p.split("=", 1) for p in raw.split("&"))
    except ValueError:
        raise ValueError(
            f"Formato de --params invalido: '{raw}'. "
            'Usa el formato "clave=valor&clave2=valor2"'
        )


def _save_last_params(job_name: str, params: dict) -> None:
    """Persiste los params en config/<job>/last_params.json para reutilizarlos en la proxima ejecucion."""
    path = _PROJECT_ROOT / "config" / job_name / _LAST_PARAMS_FILENAME
    path.write_text(json.dumps(params, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info(f"Params guardados en {path}")


def _load_last_params(job_name: str) -> dict:
    """Carga los params persistidos de la ultima ejecucion. Retorna dict vacio si no existen."""
    path = _PROJECT_ROOT / "config" / job_name / _LAST_PARAMS_FILENAME
    if not path.exists():
        return {}
    params = json.loads(path.read_text(encoding="utf-8"))
    logger.info(f"Params cargados de ejecucion anterior: {params}")
    return params


def _run_full(scrape_fn, process_fn, settings, job_name: str, now: datetime, params: dict) -> list[dict]:
    """Flujo completo: scraping → raw → (proceso opcional) → limpieza de raw."""
    logger.info("Iniciando scraper...")
    if params:
        logger.info(f"Parametros recibidos: {params}")

    web_config = load_web_config(job_name)
    driver = DriverConfig(**settings.DRIVER_CONFIG).get_driver()

    try:
        datos = scrape_fn(driver, web_config, params)
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

    try:
        if skip_process:
            logger.info("skip_process=True: omitiendo process.py, usando raw directamente")
            processed = raw_records
        else:
            processed = process_fn(pd.DataFrame(raw_records))
    finally:
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

    if args.params:
        params = _parse_params(args.params)
        _save_last_params(job_name, params)
    else:
        params = _load_last_params(job_name)

    try:
        if args.reprocess:
            processed = _run_reprocess(args.reprocess, process_fn, settings)
        else:
            processed = _run_full(scrape_fn, process_fn, settings, job_name, now, params)

        _save_output(processed, settings, now)

    except Exception as e:
        logger.error(f"Error durante la ejecucion: {e}", exc_info=True)
        raise
