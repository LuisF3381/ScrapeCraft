import pytest
import os
import re
import pandas as pd
from unittest.mock import MagicMock
from urllib.parse import urlparse
from src.shared.driver_config import create_driver
from src.shared.job_runner import load_web_config as _load_web_config
from src.books_to_scrape.process import process
from src.books_to_scrape.utils import safe_get_text, safe_get_attr, parse_record
from src.books_to_scrape import settings


def load_web_config():
    return _load_web_config("books_to_scrape")


class TestWebConfig:
    """Tests para validar el archivo web_config.yaml"""

    def test_web_config_file_exists(self):
        """Verifica que existe el archivo web_config.yaml."""
        assert os.path.exists("src/books_to_scrape/web_config.yaml"), "No existe src/books_to_scrape/web_config.yaml"
        print("[OK] src/books_to_scrape/web_config.yaml existe")

    def test_web_config_has_required_keys(self):
        """Verifica que el YAML tiene las claves requeridas."""
        web_config = load_web_config()
        assert "url" in web_config, "Falta 'url' en web_config.yaml"
        assert "xpath_selectors" in web_config, "Falta 'xpath_selectors' en web_config.yaml"
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

    def test_xpath_selectors_has_container(self):
        """Verifica que existe el selector 'container' (obligatorio en el sistema)."""
        web_config = load_web_config()
        selectors = web_config["xpath_selectors"]
        assert "container" in selectors, "Falta selector 'container' en xpath_selectors"
        print("[OK] Selector 'container' presente")

    def test_xpath_selectors_format(self):
        """Verifica que los selectores XPath tienen formato válido."""
        web_config = load_web_config()
        selectors = web_config["xpath_selectors"]
        xpath_pattern = re.compile(r"^(\.?//|/)")

        for name, xpath in selectors.items():
            assert xpath_pattern.match(xpath), f"XPath inválido para '{name}': {xpath} (debe empezar con / o // o .//)"
            print(f"[OK] XPath válido para '{name}'")

    def test_xpath_selectors_has_expected_fields(self):
        """Verifica que existen los selectores de los campos configurados."""
        web_config = load_web_config()
        selectors = web_config["xpath_selectors"]
        expected_fields = ["Titulo", "Precio", "Rating"]
        for field in expected_fields:
            assert field in selectors, f"Falta selector para el campo '{field}'"
            print(f"[OK] Selector presente para '{field}'")

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
        """Verifica que STORAGE_CONFIG tiene las claves requeridas."""
        required_keys = ["output_folder", "filename", "naming_mode"]
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

    def test_storage_config_output_formats_are_valid(self):
        """Verifica que los formatos de salida son válidos."""
        valid_formats = ["csv", "json", "xml", "xlsx"]
        formats = settings.STORAGE_CONFIG.get("output_formats", [])
        assert len(formats) > 0, "output_formats no puede estar vacío"
        for fmt in formats:
            assert fmt in valid_formats, f"Formato inválido: '{fmt}'. Debe ser uno de {valid_formats}"
        print(f"[OK] Formatos de salida válidos: {formats}")


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
        test_config = settings.DRIVER_CONFIG.copy()
        test_config['headless'] = True

        driver = create_driver(test_config)

        try:
            assert driver is not None
            print("[OK] Driver inicializado correctamente con configuración de settings.py")
        finally:
            driver.quit()


class TestRawConfig:
    """Tests para validar RAW_CONFIG en settings.py"""

    def test_settings_has_raw_config(self):
        """Verifica que settings.py tiene RAW_CONFIG."""
        assert hasattr(settings, 'RAW_CONFIG')
        assert isinstance(settings.RAW_CONFIG, dict)
        print("[OK] settings.py contiene RAW_CONFIG")

    def test_raw_config_has_required_keys(self):
        """Verifica que RAW_CONFIG tiene las claves requeridas."""
        required_keys = ["raw_folder", "filename", "format", "retention"]
        for key in required_keys:
            assert key in settings.RAW_CONFIG, f"Falta '{key}' en RAW_CONFIG"
        print("[OK] RAW_CONFIG tiene todas las claves requeridas")

    def test_raw_config_format_is_valid(self):
        """Verifica que el formato raw es uno de los soportados."""
        valid_formats = ["csv", "json", "xml", "xlsx"]
        fmt = settings.RAW_CONFIG["format"]
        assert fmt in valid_formats, f"Formato raw invalido: '{fmt}'. Debe ser uno de {valid_formats}"
        print(f"[OK] Formato raw valido: {fmt}")

    def test_raw_config_retention_mode_is_valid(self):
        """Verifica que el modo de retencion es valido."""
        valid_modes = ["keep_all", "keep_last_n", "keep_days"]
        mode = settings.RAW_CONFIG["retention"]["mode"]
        assert mode in valid_modes, f"Modo invalido: {mode}. Debe ser uno de {valid_modes}"
        print(f"[OK] Modo de retencion valido: {mode}")


class TestProcess:
    """Tests unitarios para process.py de books_to_scrape."""

    def _make_df(self, rows: list[dict]) -> pd.DataFrame:
        return pd.DataFrame(rows).astype(str).replace("nan", "")

    def test_process_returns_list_of_dicts(self):
        """Verifica que process() retorna una lista de diccionarios."""
        df = self._make_df([
            {"Numero": "1", "Titulo": "A Book", "Precio": "£12.99", "Rating": "star-rating Three"}
        ])
        result = process(df)
        assert isinstance(result, list)
        assert isinstance(result[0], dict)
        print("[OK] process() retorna list[dict]")

    def test_process_precio_gbp_conversion(self):
        """Verifica que Precio_GBP extrae el valor numérico correctamente."""
        df = self._make_df([
            {"Numero": "1", "Titulo": "Book A", "Precio": "£51.77", "Rating": "star-rating One"},
            {"Numero": "2", "Titulo": "Book B", "Precio": "£10.00", "Rating": "star-rating Two"},
        ])
        result = process(df)
        assert result[0]["Precio_GBP"] == 51.77, f"Esperado 51.77, obtenido {result[0]['Precio_GBP']}"
        assert result[1]["Precio_GBP"] == 10.00, f"Esperado 10.00, obtenido {result[1]['Precio_GBP']}"
        print("[OK] Precio_GBP se convierte correctamente")

    def test_process_rating_numerico_conversion(self):
        """Verifica que Rating_Numerico mapea correctamente las 5 estrellas."""
        casos = [
            ("star-rating One",   1),
            ("star-rating Two",   2),
            ("star-rating Three", 3),
            ("star-rating Four",  4),
            ("star-rating Five",  5),
        ]
        for rating_raw, esperado in casos:
            df = self._make_df([
                {"Numero": "1", "Titulo": "X", "Precio": "£1.00", "Rating": rating_raw}
            ])
            result = process(df)
            assert result[0]["Rating_Numerico"] == esperado, (
                f"Rating '{rating_raw}': esperado {esperado}, obtenido {result[0]['Rating_Numerico']}"
            )
        print("[OK] Rating_Numerico mapea correctamente los 5 valores")

    def test_process_precio_empty_returns_none(self):
        """Verifica que un Precio vacío produce None en Precio_GBP."""
        df = self._make_df([
            {"Numero": "1", "Titulo": "Book", "Precio": "", "Rating": "star-rating One"}
        ])
        result = process(df)
        assert result[0]["Precio_GBP"] is None, f"Precio vacío debe dar None, obtenido {result[0]['Precio_GBP']}"
        print("[OK] Precio vacío produce None en Precio_GBP")

    def test_process_preserves_all_records(self):
        """Verifica que process() no descarta ni duplica registros."""
        rows = [
            {"Numero": str(i), "Titulo": f"Book {i}", "Precio": f"£{i}.99", "Rating": "star-rating One"}
            for i in range(1, 6)
        ]
        df = self._make_df(rows)
        result = process(df)
        assert len(result) == 5, f"Esperado 5 registros, obtenidos {len(result)}"
        print("[OK] process() preserva el número de registros")


class TestUtils:
    """Tests unitarios para utils.py de books_to_scrape."""

    def _mock_element(self, text: str = "", attrs: dict | None = None):
        """Crea un WebElement mock con texto y atributos configurables."""
        element = MagicMock()
        element.text = text
        element.get_attribute = lambda attr: (attrs or {}).get(attr, None)
        return element

    def test_safe_get_text_returns_text(self):
        """Verifica que safe_get_text devuelve el texto del elemento."""
        child = self._mock_element(text="  £51.77  ")
        parent = MagicMock()
        parent.find_element.return_value = child

        result = safe_get_text(parent, ".//p")
        assert result == "£51.77"
        print("[OK] safe_get_text devuelve texto limpio")

    def test_safe_get_text_fallback_on_missing(self):
        """Verifica que safe_get_text retorna fallback si el elemento no existe."""
        from selenium.common.exceptions import NoSuchElementException
        parent = MagicMock()
        parent.find_element.side_effect = NoSuchElementException

        result = safe_get_text(parent, ".//p", fallback="N/A")
        assert result == "N/A"
        print("[OK] safe_get_text retorna fallback cuando el elemento no existe")

    def test_safe_get_attr_returns_attribute(self):
        """Verifica que safe_get_attr devuelve el atributo solicitado."""
        child = self._mock_element(attrs={"title": "A Light in the Attic"})
        parent = MagicMock()
        parent.find_element.return_value = child

        result = safe_get_attr(parent, ".//h3/a", "title")
        assert result == "A Light in the Attic"
        print("[OK] safe_get_attr devuelve el atributo correctamente")

    def test_safe_get_attr_fallback_on_missing(self):
        """Verifica que safe_get_attr retorna fallback si el elemento no existe."""
        from selenium.common.exceptions import NoSuchElementException
        parent = MagicMock()
        parent.find_element.side_effect = NoSuchElementException

        result = safe_get_attr(parent, ".//h3/a", "title", fallback="")
        assert result == ""
        print("[OK] safe_get_attr retorna fallback cuando el elemento no existe")

    def test_parse_record_includes_numero(self):
        """Verifica que parse_record añade el campo Numero."""
        selectors = {
            "container": "//article",
            "Titulo": ".//h3/a",
            "Precio": ".//p",
            "Rating": ".//p[@class]",
        }
        item = MagicMock()
        item.find_element.return_value = MagicMock(
            text="£10.00",
            get_attribute=lambda attr: "star-rating Two" if attr == "class" else "A Book"
        )

        record = parse_record(item, selectors, index=3)
        assert record["Numero"] == 3
        assert "container" not in record
        print("[OK] parse_record incluye Numero y omite 'container'")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
