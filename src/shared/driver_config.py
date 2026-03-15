import logging
from seleniumbase import Driver

logger: logging.Logger = logging.getLogger(__name__)


class DriverConfig:
    """Configuracion para inicializar el driver de SeleniumBase con opciones personalizables."""

    def __init__(
        self,
        headless: bool = False,
        undetected: bool = True,
        maximize: bool = True,
        window_size: tuple[int, int] | None = None,
        user_agent: str | None = None,
        proxy: str | None = None
    ) -> None:
        """
        Inicializa la configuracion del driver.

        Args:
            headless: Ejecutar en modo sin interfaz grafica. Default: False
            undetected: Activar undetected-chromedriver para evadir deteccion. Default: True
            maximize: Maximizar la ventana del navegador. Default: True
            window_size: Tupla (ancho, alto) para establecer tamano especifico. Default: None
            user_agent: User agent personalizado. Default: None
            proxy: Servidor proxy en formato "ip:puerto". Default: None
        """
        self.headless: bool = headless
        self.undetected: bool = undetected
        self.maximize: bool = maximize
        self.window_size: tuple[int, int] | None = window_size
        self.user_agent: str | None = user_agent
        self.proxy: str | None = proxy

    def get_driver(self) -> Driver:
        """
        Crea y retorna un driver de SeleniumBase configurado con las opciones especificadas.

        Returns:
            Driver: Instancia del driver de SeleniumBase configurada.
        """
        driver_kwargs: dict = {
            'uc': self.undetected,
            'headless': self.headless
        }

        if self.user_agent:
            driver_kwargs['user_agent'] = self.user_agent

        if self.proxy:
            driver_kwargs['proxy'] = self.proxy

        try:
            driver: Driver = Driver(**driver_kwargs)
        except Exception as e:
            raise RuntimeError(
                f"No se pudo inicializar el driver de SeleniumBase: {e}\n"
                "Verifica que Google Chrome este instalado y que el puerto no este bloqueado."
            ) from e

        logger.info("Driver inicializado correctamente")

        try:
            if self.window_size:
                width, height = self.window_size
                driver.set_window_size(width, height)
            elif self.maximize:
                driver.maximize_window()
        except Exception as e:
            driver.quit()
            raise RuntimeError(f"Error al configurar la ventana del driver: {e}") from e

        return driver
