from pathlib import Path
from src.books_to_scrape.scraper import scrape
from src.books_to_scrape.process import process
from config.books_to_scrape import settings
from src.shared.job_runner import run as _run_job

_JOB_NAME = Path(__file__).parent.name


def run(args):
    _run_job(args, scrape, process, settings, _JOB_NAME)
