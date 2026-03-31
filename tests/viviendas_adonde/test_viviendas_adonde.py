import pytest
import os
import re
from urllib.parse import urlparse
from src.shared.driver_config import create_driver
from src.shared.job_runner import load_web_config as _load_web_config
from src.viviendas_adonde import settings


def load_web_config():
    return _load_web_config("viviendas_adonde")


class TestWebConfig:
    """Tests para validar el archivo web_config.yaml"""

    def test_web_config_file_exists(self):
        """Verifica que existe el archivo web_config.yaml."""
        assert os.path.exists("src/viviendas_adonde/web_config.yaml"), "No existe src/viviendas_adonde/web_config.yaml"
        print("[OK] src/viviendas_adonde/web_config.yaml existe")

    def test_web_config_has_required_keys(self):
        """Verifica que el YAML tiene las claves requeridas."""
        web_config = load_web_config()
        assert "url" in web_config, "Falta 'url' en web_config.yaml"
        assert "selectors" in web_config, "Falta 'selectors' en web_config.yaml"
        assert "waits" in web_config, "Falta 'waits' en web_config.yaml"
        print("[OK] web_config.yaml tiene todas las claves requeridas")

    def test_url_format_is_valid(self):
        """Verifica que la URL tiene formato válido."""
        web_config = load_web_config()
        url = web_config["url"]
        parsed = urlparse(url)
        assert parsed.scheme in ("http", "https"), f"URL debe empezar con http/https: {url}"
        assert parsed.netloc, f"URL no tiene dominio válido: {url}"
        print(f"[OK] URL válida: {url}")

    def test_selectors_format(self):
        """Verifica que los selectores tienen formato válido (XPath o CSS)."""
        web_config = load_web_config()
        selectors = web_config["selectors"]
        xpath_pattern = re.compile(r"^(\.?//|/)")

        for name, value in selectors.items():
            assert isinstance(value, str) and value.strip(), f"Selector vacío o inválido para '{name}'"
            if xpath_pattern.match(value):
                print(f"[OK] Selector XPath válido para '{name}'")
            else:
                print(f"[OK] Selector CSS para '{name}': {value}")

    def test_waits_are_positive_numbers(self):
        """Verifica que los waits son números positivos."""
        web_config = load_web_config()
        waits = web_config["waits"]

        assert waits.get("reconnect_attempts", 0) > 0, "reconnect_attempts debe ser > 0"
        assert waits.get("after_load", 0) >= 0, "after_load debe ser >= 0"
        print("[OK] Waits tienen valores válidos")


class TestStorageConfig:
    """Tests para validar STORAGE_CONFIG en settings.py"""

    def test_settings_has_storage_config(self):
        """Verifica que settings.py tiene STORAGE_CONFIG."""
        assert hasattr(settings, 'STORAGE_CONFIG')
        assert isinstance(settings.STORAGE_CONFIG, dict)
        print("[OK] settings.py contiene STORAGE_CONFIG")

    def test_storage_config_has_required_keys(self):
        """Verifica que STORAGE_CONFIG tiene todas las claves requeridas."""
        required_keys = ["output_folder", "filename", "naming_mode", "output_formats",
                         "raw_folder", "retention", "format_config"]
        for key in required_keys:
            assert key in settings.STORAGE_CONFIG, f"Falta '{key}' en STORAGE_CONFIG"
        print("[OK] STORAGE_CONFIG tiene todas las claves requeridas")

    def test_storage_config_naming_mode_is_valid(self):
        """Verifica que naming_mode es válido."""
        valid_modes = ["overwrite", "date_suffix", "timestamp_suffix", "date_folder"]
        mode = settings.STORAGE_CONFIG["naming_mode"]
        assert mode in valid_modes, f"Modo inválido: {mode}. Debe ser uno de {valid_modes}"
        print(f"[OK] Modo de nombrado válido: {mode}")

    def test_storage_config_output_folder_is_valid_path(self):
        """Verifica que output_folder es una ruta valida no vacia."""
        folder = settings.STORAGE_CONFIG["output_folder"]
        assert isinstance(folder, str) and folder.strip(), "output_folder debe ser una cadena no vacia"
        print(f"[OK] output_folder configurado: {folder}")

    def test_storage_config_raw_folder_is_valid_path(self):
        """Verifica que raw_folder es una ruta valida no vacia."""
        folder = settings.STORAGE_CONFIG["raw_folder"]
        assert isinstance(folder, str) and folder.strip(), "raw_folder debe ser una cadena no vacia"
        print(f"[OK] raw_folder configurado: {folder}")

    def test_storage_config_output_formats_are_valid(self):
        """Verifica que los formatos de salida son válidos."""
        valid_formats = ["csv", "json", "xml", "xlsx"]
        formats = settings.STORAGE_CONFIG.get("output_formats", [])
        assert len(formats) > 0, "output_formats no puede estar vacío"
        for fmt in formats:
            assert fmt in valid_formats, f"Formato inválido: '{fmt}'. Debe ser uno de {valid_formats}"
        print(f"[OK] Formatos de salida válidos: {formats}")

    def test_storage_config_retention_mode_is_valid(self):
        """Verifica que el modo de retencion es valido."""
        valid_modes = ["keep_all", "keep_last_n", "keep_days"]
        mode = settings.STORAGE_CONFIG["retention"]["mode"]
        assert mode in valid_modes, f"Modo invalido: {mode}. Debe ser uno de {valid_modes}"
        print(f"[OK] Modo de retencion valido: {mode}")

    def test_storage_config_format_config_covers_output_formats(self):
        """Verifica que format_config define config para cada formato en output_formats."""
        valid_formats = ["csv", "json", "xml", "xlsx"]
        output_formats = settings.STORAGE_CONFIG.get("output_formats", [])
        format_config = settings.STORAGE_CONFIG.get("format_config", {})
        assert isinstance(format_config, dict) and format_config, \
            "format_config debe ser un dict no vacio"
        for fmt in output_formats:
            assert fmt in format_config, \
                f"format_config no define config para el formato '{fmt}'. " \
                f"Agrega una entrada '{fmt}' en STORAGE_CONFIG['format_config']"
            assert isinstance(format_config[fmt], dict) and format_config[fmt], \
                f"format_config['{fmt}'] debe ser un dict no vacio"
            assert fmt in valid_formats, f"Formato invalido en format_config: '{fmt}'"
            print(f"[OK] format_config['{fmt}'] configurado correctamente")


class TestDriverConfig:
    """Tests para verificar que el driver se inicializa correctamente con settings.py"""

    def test_settings_file_has_driver_config(self):
        """Verifica que settings.py tiene la configuración DRIVER_CONFIG."""
        assert hasattr(settings, 'DRIVER_CONFIG')
        assert isinstance(settings.DRIVER_CONFIG, dict)
        print("[OK] settings.py contiene DRIVER_CONFIG")

    def test_driver_instance_created_with_settings_file(self):
        """
        TEST PRINCIPAL: Verifica que se puede crear una instancia del driver
        con la configuración exacta de settings.py
        """
        # Modificar temporalmente para modo headless (más rápido en tests)
        test_config = settings.DRIVER_CONFIG.copy()
        test_config['headless'] = True

        driver = create_driver(test_config)

        try:
            assert driver is not None
            print("[OK] Driver inicializado correctamente con configuración de settings.py")
        finally:
            driver.quit()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
