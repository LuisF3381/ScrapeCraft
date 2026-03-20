import logging
import time
from selenium.webdriver.common.by import By
from seleniumbase import Driver
from src.books_to_scrape.utils import parse_record

logger = logging.getLogger(__name__)


def scrape(driver: Driver, web_config: dict, params: dict = None) -> list[dict]:
    """
    Extrae datos de la primera pagina de books.toscrape.com.

    Args:
        driver:     Instancia del driver de SeleniumBase
        web_config: Diccionario con url, xpath_selectors y waits
        params:     Parametros opcionales pasados por CLI (ej: {"categoria": "mystery"})

    Returns:
        list[dict]: Lista de diccionarios con Numero, Titulo, Precio y Rating
    """
    params = params or {}
    url: str = web_config["url"]
    selectors: dict = web_config["xpath_selectors"]
    waits: dict = web_config["waits"]

    # --- Navegacion y carga de pagina ---
    # books.toscrape.com es un sitio estatico de practica, no requiere UC mode
    driver.open(url)
    logger.info("Pagina cargada correctamente")
    time.sleep(waits["after_load"])

    # --- Extraccion de elementos ---
    items = driver.find_elements(By.XPATH, selectors["container"])
    logger.info(f"Encontrados {len(items)} libros")

    # --- Construccion de registros ---
    datos: list[dict] = [
        parse_record(item, selectors, index)
        for index, item in enumerate(items, start=1)
    ]

    return datos
