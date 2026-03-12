import logging
import time
from selenium.webdriver.common.by import By
from seleniumbase import Driver
from src.viviendas_adonde.utils import parse_record

logger = logging.getLogger(__name__)


def scrape(driver: Driver, web_config: dict) -> list[dict]:
    """
    Extrae datos desde la URL usando los selectores del archivo de configuracion.

    Args:
        driver:     Instancia del driver de SeleniumBase
        web_config: Diccionario con url, xpath_selectors y waits

    Returns:
        list[dict]: Lista de diccionarios con los datos extraidos
    """
    url: str = web_config["url"]
    selectors: dict = web_config["xpath_selectors"]
    waits: dict = web_config["waits"]

    # --- Navegacion y carga de pagina ---
    driver.uc_open_with_reconnect(url, waits["reconnect_attempts"])
    driver.uc_gui_handle_captcha()
    logger.info("Pagina cargada correctamente")
    time.sleep(waits["after_load"])

    # --- Extraccion de elementos ---
    # IMPLEMENTAR: ajustar el selector "container" en web_config.yaml
    items = driver.find_elements(By.XPATH, selectors["container"])
    logger.info(f"Encontrados {len(items)} elementos")

    # --- Construccion de registros ---
    # IMPLEMENTAR: agregar logica personalizada en utils.py si se necesita
    #              tratamiento especial por campo (paginacion, campos opcionales, etc.)
    datos: list[dict] = [
        parse_record(item, selectors, index)
        for index, item in enumerate(items, start=1)
    ]

    return datos
