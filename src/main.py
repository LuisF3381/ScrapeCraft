import argparse
import importlib
import os


def get_available_jobs() -> list[str]:
    """Escanea src/ y retorna los jobs disponibles (carpetas con app_job.py)."""
    src_path = os.path.dirname(__file__)
    return [
        entry.name
        for entry in os.scandir(src_path)
        if entry.is_dir() and os.path.isfile(os.path.join(entry.path, "app_job.py"))
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description="ScrapeCraft - Web scraper multi-job")
    parser.add_argument(
        "--job",
        metavar="JOB",
        help="Job a ejecutar (ej: viviendas_adonde)"
    )
    parser.add_argument(
        "--reprocess",
        metavar="SUFFIX",
        help="Reprocesar raw existente indicando su sufijo (ej: 20260312_143052)"
    )
    parser.add_argument(
        "--params",
        metavar="PARAMS",
        default=None,
        help='Parametros para el scraper en formato "clave=valor&clave2=valor2" (ej: "fecha=01/12/2024&pais=peru")'
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Listar los jobs disponibles"
    )
    args = parser.parse_args()

    if args.list:
        jobs = get_available_jobs()
        if jobs:
            print("Jobs disponibles:")
            for job in jobs:
                print(f"  - {job}")
        else:
            print("No se encontraron jobs. Crea uno en src/<nombre>/app_job.py")
        raise SystemExit(0)

    if not args.job:
        parser.error("Se requiere --job para ejecutar un proceso. Usa --list para ver los disponibles.")

    try:
        job_module = importlib.import_module(f"src.{args.job}.app_job")
    except ModuleNotFoundError:
        jobs = get_available_jobs()
        available = ", ".join(jobs) if jobs else "ninguno"
        print(f"Error: job '{args.job}' no encontrado. Jobs disponibles: {available}")
        raise SystemExit(1)

    job_module.run(args)


if __name__ == "__main__":
    main()
