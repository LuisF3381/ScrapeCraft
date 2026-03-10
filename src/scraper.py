import logging
import time
from selenium.webdriver.common.by import By
from seleniumbase import Driver


def scrape(driver: Driver, web_config: dict, logger: logging.Logger) -> list[dict]:
    """
    Extrae datos desde la URL usando los selectores del archivo de configuracion.

    Args:
        driver: Instancia del driver de SeleniumBase
        web_config: Diccionario con url, xpath_selectors y waits
        logger: Logger para registrar eventos

    Returns:
        list: Lista de diccionarios con los datos extraidos
    """
    # Obtienen los parametros para la ejecucion del proceso de scraping
    url: str = web_config["url"]
    selectors: dict = web_config["xpath_selectors"]
    waits: dict = web_config["waits"]

    # Estructura de datos para almacenar los resultados
    datos: list[dict] = []

    # Navegacion a la pagina 
    driver.uc_open_with_reconnect(url, waits["reconnect_attempts"])
    driver.uc_gui_handle_captcha()
    logger.info("Pagina cargada correctamente")

    time.sleep(waits["after_load"])

    # Proceso de extraccion de datos
    items = driver.find_elements(By.XPATH, selectors["container"])
    logger.info(f"Encontrados {len(items)} elementos")

    for i, item in enumerate(items, 1):
        registro: dict = {"Numero": i}
        for field_name, field_xpath in selectors.items():
            if field_name == "container":
                continue
            text = item.find_element(By.XPATH, field_xpath).text
            registro[field_name] = text.replace("\n", " | ").strip()
        datos.append(registro)

    # Registro de informacion sobre el proceso de scraping
    return datos
