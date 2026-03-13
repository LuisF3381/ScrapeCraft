from pathlib import Path
from src.viviendas_adonde.scraper import scrape
from src.viviendas_adonde.process import process
from config.viviendas_adonde import settings
from src.shared.job_runner import run as _run_job

_JOB_NAME = Path(__file__).parent.name


def run(args):
    _run_job(args, scrape, process, settings, _JOB_NAME)
