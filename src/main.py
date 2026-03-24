import argparse
import importlib
import logging
import yaml
from pathlib import Path
from src.shared import job_runner

# Nombre explicito para que propague a "src" tanto al ejecutar con -m como al importar
logger = logging.getLogger("src.main")


def _setup_console_handler() -> None:
    """Configura un handler de consola en el logger 'src' para mensajes del
    orquestador (serie, pipeline). setup_logger() de cada job reemplaza todos
    los handlers cuando arranca, por lo que este no genera duplicados."""
    src_logger = logging.getLogger("src")
    src_logger.setLevel(logging.INFO)
    src_logger.propagate = False
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(message)s"))
    src_logger.addHandler(handler)


def get_available_jobs() -> list[str]:
    """Escanea src/ y retorna los jobs disponibles (carpetas con scraper.py)."""
    src_path = Path(__file__).parent
    return [
        entry.name
        for entry in src_path.iterdir()
        if entry.is_dir() and (entry / "scraper.py").is_file()
    ]


def _load_job_parts(job_name: str) -> tuple:
    """Importa y retorna (scrape_fn, process_fn, settings) del job indicado."""
    try:
        scraper  = importlib.import_module(f"src.{job_name}.scraper")
        process  = importlib.import_module(f"src.{job_name}.process")
        settings = importlib.import_module(f"src.{job_name}.settings")
        return scraper.scrape, process.process, settings
    except ModuleNotFoundError:
        available = ", ".join(get_available_jobs()) or "ninguno"
        logger.error(f"Job '{job_name}' no encontrado. Jobs disponibles: {available}")
        raise SystemExit(1)


def _make_args(job_name: str) -> argparse.Namespace:
    """Construye un Namespace de args para un job individual dentro de una serie."""
    return argparse.Namespace(
        job=job_name,
        pipeline=None,
        reprocess=None,
    )


def _run_series(job_entries: list[dict]) -> None:
    """
    Ejecuta una lista de jobs en serie.
    Cada entrada es un dict con claves: name (str), params (dict), reprocess (str|None).
    Si un job falla, registra el error y continua con el siguiente.
    """
    total = len(job_entries)
    failed = []

    for i, entry in enumerate(job_entries, start=1):
        job_name = entry["name"]
        params   = entry.get("params") or {}
        logger.info(f"\n[{i}/{total}] Iniciando job: {job_name}")

        try:
            scrape_fn, process_fn, settings = _load_job_parts(job_name)
            job_runner.run(_make_args(job_name), scrape_fn, process_fn, settings, job_name, params=params)
        except SystemExit:
            raise
        except Exception as e:
            logger.error(f"[{i}/{total}] ERROR en '{job_name}': {e}")
            failed.append(job_name)

    logger.info(f"\n{'='*50}")
    logger.info(f"Serie finalizada: {total - len(failed)}/{total} jobs exitosos")
    if failed:
        logger.warning(f"Jobs con error: {', '.join(failed)}")


def _load_pipeline(path: str) -> list[dict]:
    """
    Carga un pipeline YAML y retorna la lista de entradas de jobs.

    Formato esperado:
        name: mi_pipeline           # opcional
        description: "..."          # opcional

        jobs:
          - name: books_to_scrape
            params:                 # opcional, dict nativo YAML
              categoria: mystery
              pagina: 1
            enabled: false          # opcional, omitir o poner true para ejecutar
          - name: viviendas_adonde
    """
    pipeline_path = Path(path)
    if not pipeline_path.is_file():
        logger.error(f"Pipeline '{path}' no encontrado.")
        raise SystemExit(1)

    with pipeline_path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "jobs" not in data or not isinstance(data["jobs"], list):
        logger.error(f"El pipeline '{path}' debe tener una clave 'jobs' con una lista de jobs.")
        raise SystemExit(1)

    if "name" in data:
        desc = f" — {data['description']}" if "description" in data else ""
        logger.info(f"Pipeline: {data['name']}{desc}")

    entries = []
    for item in data["jobs"]:
        if "name" not in item:
            logger.error("Cada job del pipeline debe tener un campo 'name'.")
            raise SystemExit(1)
        if item.get("enabled", True) is False:
            logger.info(f"Job '{item['name']}' desactivado (enabled: false), omitiendo.")
            continue
        entries.append({
            "name":   item["name"],
            "params": item.get("params") or {},
        })

    return entries


def main() -> None:
    _setup_console_handler()

    parser = argparse.ArgumentParser(description="ScrapeCraft - Web scraper multi-job")

    # --- Modos de ejecucion (mutuamente excluyentes) ---
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--job",
        metavar="JOB",
        help="Ejecutar un job individual (ej: books_to_scrape)"
    )
    mode_group.add_argument(
        "--pipeline",
        metavar="YAML",
        help="Ejecutar un pipeline definido en un archivo YAML (ej: config/pipelines/diario.yaml)"
    )

    # --- Opciones exclusivas de --job ---
    parser.add_argument(
        "--reprocess",
        metavar="SUFFIX",
        help="Solo con --job: reprocesar raw existente por sufijo (ej: 20260312_143052)"
    )

    # --- Utilidades ---
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar los jobs disponibles"
    )

    args = parser.parse_args()

    # --list
    if args.list:
        jobs = get_available_jobs()
        if jobs:
            print("Jobs disponibles:")
            for job in jobs:
                print(f"  - {job}")
        else:
            print("No se encontraron jobs. Crea uno en src/<nombre>/scraper.py")
        raise SystemExit(0)

    # --reprocess es exclusivo de --job
    if args.reprocess and not args.job:
        parser.error("--reprocess solo puede usarse junto a --job.")

    # --- Despacho segun modo ---

    if args.job:
        scrape_fn, process_fn, settings = _load_job_parts(args.job)
        job_runner.run(args, scrape_fn, process_fn, settings, args.job)

    elif args.pipeline:
        entries = _load_pipeline(args.pipeline)
        logger.info(f"Pipeline '{args.pipeline}': {len(entries)} job(s)")
        _run_series(entries)

    else:
        parser.error("Especifica un modo de ejecucion: --job o --pipeline. Usa --list para ver los jobs disponibles.")


if __name__ == "__main__":
    main()
