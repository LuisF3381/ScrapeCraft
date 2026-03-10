import logging
import yaml
from src.driver_config import DriverConfig
from src.logger import setup_logger
from src.scraper import scrape
from src.storage import save_data
from config import settings


def load_web_config(logger: logging.Logger | None = None, path: str = "config/web_config.yaml") -> dict:
    """Carga la configuracion de la web desde el archivo YAML."""
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if logger:
        logger.info(f"Configuracion cargada: {config['url']}")
    return config


def main() -> None:
    logger = setup_logger(**settings.LOG_CONFIG)
    logger.info("Iniciando scraper...")

    try:
        # Configuracion del driver
        web_config = load_web_config(logger)
        driver_config = DriverConfig(**settings.DRIVER_CONFIG)
        driver = driver_config.get_driver()

        try:
            # Proceso de Scraping
            datos = scrape(driver, web_config, logger)

            # Escritura de los resultados en los formatos configurados
            output_formats = settings.STORAGE_CONFIG.get("output_formats", ["csv"])
            for formato in output_formats:
                save_data(datos, formato, settings.DATA_CONFIG, settings.STORAGE_CONFIG)
        finally:
            driver.quit()

        logger.info("Scraper finalizado")
    except Exception as e:
        logger.error(f"Error durante la ejecucion: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
