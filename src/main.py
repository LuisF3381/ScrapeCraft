import argparse
import importlib
import os
import types
import yaml


def get_available_jobs() -> list[str]:
    """Escanea src/ y retorna los jobs disponibles (carpetas con app_job.py)."""
    src_path = os.path.dirname(__file__)
    return [
        entry.name
        for entry in os.scandir(src_path)
        if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "app_job.py"))
    ]


def _load_job_module(job_name: str) -> types.ModuleType:
    """Importa y retorna el modulo app_job del job indicado."""
    try:
        return importlib.import_module(f"src.{job_name}.app_job")
    except ModuleNotFoundError:
        available = ", ".join(get_available_jobs()) or "ninguno"
        print(f"Error: job '{job_name}' no encontrado. Jobs disponibles: {available}")
        raise SystemExit(1)


def _make_args(job_name: str, params: str | None = None, reprocess: str | None = None) -> argparse.Namespace:
    """Construye un Namespace de args para un job individual dentro de una serie."""
    return argparse.Namespace(
        job=job_name,
        jobs=None,
        all=False,
        pipeline=None,
        params=params,
        reprocess=reprocess,
    )


def _run_series(job_entries: list[dict]) -> None:
    """
    Ejecuta una lista de jobs en serie.
    Cada entrada es un dict con claves: name (str), params (str|None).
    Si un job falla, registra el error y continua con el siguiente.
    """
    total = len(job_entries)
    failed = []

    for i, entry in enumerate(job_entries, start=1):
        job_name = entry["name"]
        params   = entry.get("params")
        print(f"\n[{i}/{total}] Iniciando job: {job_name}", flush=True)

        try:
            module = _load_job_module(job_name)
            module.run(_make_args(job_name, params=params))
        except SystemExit:
            raise
        except Exception as e:
            print(f"[{i}/{total}] ERROR en '{job_name}': {e}", flush=True)
            failed.append(job_name)

    print(f"\n{'='*50}", flush=True)
    print(f"Serie finalizada: {total - len(failed)}/{total} jobs exitosos", flush=True)
    if failed:
        print(f"Jobs con error: {', '.join(failed)}", flush=True)


def _load_pipeline(path: str) -> list[dict]:
    """
    Carga un pipeline YAML y retorna la lista de entradas de jobs.

    Formato esperado:
        jobs:
          - name: books_to_scrape
            params: "categoria=mystery"   # opcional
          - name: viviendas_adonde
    """
    if not os.path.isfile(path):
        print(f"Error: pipeline '{path}' no encontrado.")
        raise SystemExit(1)

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "jobs" not in data or not isinstance(data["jobs"], list):
        print(f"Error: el pipeline '{path}' debe tener una clave 'jobs' con una lista de jobs.")
        raise SystemExit(1)

    entries = []
    for item in data["jobs"]:
        if "name" not in item:
            print(f"Error: cada job del pipeline debe tener un campo 'name'.")
            raise SystemExit(1)
        entries.append({"name": item["name"], "params": item.get("params")})

    return entries


def main() -> None:
    parser = argparse.ArgumentParser(description="ScrapeCraft - Web scraper multi-job")

    # --- Modos de ejecucion (mutuamente excluyentes) ---
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--job",
        metavar="JOB",
        help="Ejecutar un job individual (ej: books_to_scrape)"
    )
    mode_group.add_argument(
        "--jobs",
        metavar="JOB1,JOB2,...",
        help="Ejecutar varios jobs en serie, separados por coma (ej: books_to_scrape,viviendas_adonde)"
    )
    mode_group.add_argument(
        "--all",
        action="store_true",
        help="Ejecutar todos los jobs disponibles en serie"
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
    parser.add_argument(
        "--params",
        metavar="PARAMS",
        default=None,
        help='Solo con --job: parametros en formato "clave=valor&clave2=valor2"'
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
            print("No se encontraron jobs. Crea uno en src/<nombre>/app_job.py")
        raise SystemExit(0)

    # --reprocess y --params son exclusivos de --job
    if args.reprocess and not args.job:
        parser.error("--reprocess solo puede usarse junto a --job.")
    if args.params and not args.job:
        parser.error("--params solo puede usarse junto a --job. Para series usa last_params.json o define params en el YAML del pipeline.")

    # --- Despacho segun modo ---

    if args.job:
        module = _load_job_module(args.job)
        module.run(args)

    elif args.jobs:
        job_names = [j.strip() for j in args.jobs.split(",") if j.strip()]
        if not job_names:
            parser.error("--jobs no puede estar vacio.")
        _run_series([{"name": name} for name in job_names])

    elif args.all:
        job_names = sorted(get_available_jobs())
        if not job_names:
            print("No se encontraron jobs. Crea uno en src/<nombre>/app_job.py")
            raise SystemExit(0)
        print(f"Jobs a ejecutar: {', '.join(job_names)}")
        _run_series([{"name": name} for name in job_names])

    elif args.pipeline:
        entries = _load_pipeline(args.pipeline)
        print(f"Pipeline '{args.pipeline}': {len(entries)} job(s)")
        _run_series(entries)

    else:
        parser.error("Especifica un modo de ejecucion: --job, --jobs, --all o --pipeline. Usa --list para ver los jobs disponibles.")


if __name__ == "__main__":
    main()
