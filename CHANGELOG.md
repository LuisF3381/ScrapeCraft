# Changelog

## [0.22.0] - 2026-03-13

### Fixed
- `driver_config.py`: logger cambiado de `"scrapecraft"` a `logging.getLogger(__name__)` — el logger anterior era un nodo huerfano fuera de la jerarquia `"src"`, por lo que sus mensajes se perdian silenciosamente sin llegar al archivo de log ni a la consola
- `storage.py` `_write_df()`: `df.astype(str)` ahora incluye `.replace("nan", "")` para evitar que valores `None`/`NaN` se persistan como el string literal `"nan"`, corrompiendo los datos al releerlos
- `storage.py` `cleanup_raw()` modo `keep_days`: reemplazado `os.path.getmtime()` por extraccion del timestamp del nombre del archivo, consistente con el comportamiento de `keep_last_n` y resistente a cambios de `mtime` por copias, backups o sincronizacion en la nube
- `storage.py` `cleanup_raw()` `_parse_timestamp`: ahora captura `ValueError` con `try/except` si hay archivos con nombre inesperado en la carpeta raw, emite un warning y los ignora en lugar de crashear el proceso
- `test_config.py`: `test_raw_config_format_is_csv` renombrado a `test_raw_config_format_is_valid` y corregido para validar que el formato esta en la lista de soportados (`csv | json | xml | xlsx`) en lugar de asumir siempre `"csv"`, reflejando el comportamiento real desde v0.19.0
- `app_job.py`: comentario del flujo `skip_process=True` ahora incluye `load_raw()` que estaba omitido
- `main.py`: eliminado `os.path.join()` redundante con un solo argumento en `get_available_jobs()`
- `app_job.py`: `WEB_CONFIG_PATH` ahora construido con `Path` en lugar de f-string con slashes para consistencia con el resto del modulo
- `app_job.py`: guard explicito tras `scrape()` — si el scraper retorna lista vacia lanza `RuntimeError` con mensaje descriptivo en lugar de propagar un `EmptyDataError` de pandas desde `load_raw()`

### Changed
- `process.py`: firma simplificada de `process(filename, extension, suffix, raw_config, data_config)` a `process(df: pd.DataFrame)` — la responsabilidad de cargar el raw se mueve a `app_job.py`, dejando `process.py` exclusivamente como modulo de transformacion sin logica de I/O ni imports de `storage`
- `app_job.py` `_run_full()` y `_run_reprocess()`: ahora construyen el DataFrame con `pd.DataFrame(load_raw(...))` y lo pasan directamente a `process(df)`, eliminando el round-trip innecesario `DataFrame → list[dict] → DataFrame` que ocurria cuando `process.py` llamaba a `load_raw()` internamente
- `storage.py` `build_filepath()` y `save_data()`: nuevo parametro opcional `now: datetime | None` — si se pasa, se usa como referencia temporal en lugar de llamar `datetime.now()` internamente
- `app_job.py` `_save_output()`: calcula `now = datetime.now()` una sola vez y lo propaga a todas las llamadas de `save_data()`, garantizando que todos los formatos de una misma ejecucion compartan el mismo timestamp en modo `timestamp_suffix`

### Architecture
- `process.py` queda libre de dependencias de I/O: unico import externo es `pandas`. Esto permite testearlo en aislamiento pasando un DataFrame directamente, sin necesidad de archivos en disco
- La carga del raw es ahora responsabilidad exclusiva de `app_job.py`, que ya centraliza todo el I/O del pipeline (scrape, save_raw, load_raw, cleanup_raw, save_data)

## [0.21.0] - 2026-03-12

### Changed
- Comentario de `RAW_CONFIG["format"]` en `settings.py` actualizado de "siempre csv" a "csv | json | xml | xlsx" para reflejar que el formato es configurable
- `DATA_CONFIG` documentado en README como unica fuente de verdad para parametros de formato, aplicada tanto al raw como al output

### Documentation
- Nueva tabla en README que muestra la relacion directa entre `RAW_CONFIG["format"]` y la entrada de `DATA_CONFIG` que se aplica en el pipeline completo (save_raw, load_raw, process.py)

## [0.20.0] - 2026-03-12

### Added
- `_write_df()` y `_read_df()` en `storage.py`: funciones privadas que centralizan toda la logica de lectura y escritura por formato (csv, json, xml, xlsx), eliminando la duplicacion del bloque if/elif que existia en `save_data()`, `save_raw()` y `load_raw()`
- Lineamiento **string-first**: todos los datos se persisten y se leen como `str` incondicionalmente
  - `_write_df()` aplica `df.astype(str)` antes de escribir en cualquier formato
  - `_read_df()` usa `dtype=str` al leer, evitando inferencia de tipos por parte de pandas

### Architecture
- Un unico punto de cambio para soportar un nuevo formato: agregar un bloque en `_write_df` y otro en `_read_df`
- Separacion de responsabilidades reforzada: la capa raw actua como zona de aterrizaje de strings puros; la conversion de tipos es responsabilidad exclusiva de `process.py`
- Beneficios del lineamiento string-first: preserva ceros a la izquierda, evita corte de decimales, mantiene valores danados o nulos tal cual llegan del scraper, elimina errores de inferencia de tipo en pandas

## [0.19.0] - 2026-03-12

### Changed
- `save_raw()`, `load_raw()` y `cleanup_raw()` en `storage.py` ahora respetan `raw_config["format"]` para determinar el formato del archivo raw, en lugar de asumir siempre CSV
- `process.py` ahora lee el raw segun `raw_config["format"]` usando `_read_df()`, eliminando el `pd.read_csv()` hardcodeado
- El programador puede cambiar el formato del raw a cualquiera de los soportados (csv, json, xml, xlsx) modificando unicamente `RAW_CONFIG["format"]` en `settings.py`

## [0.18.0] - 2026-03-12

### Changed
- `save_raw()`, `load_raw()` y `process.py` ahora reciben `data_config` y respetan `data_config["csv"]["encoding"]` y `data_config["csv"]["separator"]` al leer y escribir el raw, en lugar de tener valores hardcodeados
- `DATA_CONFIG` en `global_settings.py` es ahora la unica fuente de verdad para encoding y separador en todas las operaciones CSV del pipeline (raw y output)

## [0.17.0] - 2026-03-12

### Fixed
- `process.py` y `load_raw()` en `storage.py`: `pd.read_csv()` ahora especifica `encoding="utf-8"` para consistencia con `save_raw()`, que siempre guarda en UTF-8. Evita `UnicodeDecodeError` en Windows con texto en español (tildes, ñ)
- `cleanup_raw()` en `storage.py`: ordenacion de archivos cambiada de `os.path.getmtime` a `os.path.basename`, usando el timestamp del nombre de archivo como criterio de orden en lugar de la fecha de modificacion del sistema de archivos, que podia ser alterada por copias o backups

## [0.16.0] - 2026-03-12

### Changed
- `setup_logger()` en `logger.py` ahora recibe `job_name` como primer parametro y no retorna nada; el archivo de log pasa de `scrapecraft_YYYYMMDD.log` a `<job_name>_YYYYMMDD.log`
- Logger configurado sobre el nodo raiz `"src"` en lugar de `"scrapecraft"`, permitiendo que todos los modulos bajo `src.*` propaguen automaticamente sin recibir el logger como parametro
- Todos los modulos (`scraper.py`, `process.py`, `storage.py`, `app_job.py`) declaran `logger = logging.getLogger(__name__)` a nivel de modulo y eliminan `logger` de sus firmas de funcion
- `app_job.py` llama `setup_logger(_JOB_NAME, **global_settings.LOG_CONFIG)` en lugar de asignar el retorno

### Architecture
- Patron de logging cambiado de **inyeccion de dependencia** (pasar `logger` como parametro) a **logger jerarquico** (propagacion automatica via `getLogger(__name__)`)
- Cada job genera su propio archivo de log nombrado por proceso: `log/viviendas_adonde_20260312.log`, `log/otro_job_20260312.log`
- Multiples ejecuciones del mismo job en el mismo dia acumulan en el mismo archivo (append)

## [0.15.0] - 2026-03-12

### Changed
- `web_config.yaml` documentado con comentarios inline detallados: explicacion de `container` como campo reservado, sintaxis rapida de XPath, y descripcion de cada parametro de `waits`
- `WEB_CONFIG_PATH` en `app_job.py` ahora se deriva automaticamente del nombre de la carpeta del job via `Path(__file__).parent.name`, eliminando el string hardcodeado que debia actualizarse manualmente al copiar el job

## [0.14.0] - 2026-03-12

### Added
- `PIPELINE_CONFIG` en `config/<job>/settings.py` con flag `skip_process` (bool):
  - `False` (default): flujo completo con `process.py`
  - `True`: omite `process.py` y guarda el raw directamente, util cuando la web ya devuelve datos normalizados
- Funcion `load_raw()` en `storage.py`: lee un CSV raw y lo retorna como `list[dict]` sin transformaciones
- Flag `--list` en `main.py`: muestra los jobs disponibles escaneando `src/` dinamicamente
- Funcion `get_available_jobs()` en `main.py`: detecta cualquier carpeta en `src/` que contenga `app_job.py`

### Changed
- `_run_full()` en `app_job.py` bifurca segun `PIPELINE_CONFIG["skip_process"]`: llama a `process()` o a `load_raw()`
- `--job` ya no es requerido si se usa `--list`; sin argumentos muestra un mensaje guiando al usuario
- Error de job no encontrado ahora incluye la lista de jobs disponibles inline
- `save_data()`, `save_raw()` y `cleanup_raw()` en `storage.py` reciben `logger` como parametro opcional en lugar de obtenerlo internamente via `logging.getLogger()`
- Mapa del flujo ETL en `app_job.py` actualizado con el caso `skip_process=True`

### Architecture
- El pipeline ETL ahora tiene tres variantes configurables:
  - Flujo completo: `scrape → save_raw → process → cleanup_raw → save_data`
  - Sin proceso: `scrape → save_raw → cleanup_raw → save_data`
  - Reprocess: `process → save_data`

## [0.13.0] - 2026-03-12

### Added
- Nuevo modulo `src/<job>/utils.py` con funciones auxiliares de extraccion reutilizables:
  - `safe_get_text(element, xpath, fallback)`: extrae texto de un sub-elemento con manejo seguro de `NoSuchElementException`
  - `parse_record(item, selectors, index)`: construye el diccionario de un registro a partir de un elemento contenedor

### Changed
- `app_job.py` refactorizado para mayor legibilidad:
  - `run()` queda como dispatcher limpio de ~10 lineas
  - Logica extraida en funciones privadas: `_run_full()`, `_run_reprocess()`, `_save_output()`
  - Bloque de comentario con mapa visual del flujo ETL al inicio del archivo
- `scraper.py` refactorizado para usar `utils.py`:
  - For-loop de extraccion de campos reemplazado por llamada a `parse_record()`
  - Secciones marcadas con `# IMPLEMENTAR` para guiar al data engineer
- `process()` en `process.py` ahora recibe `logger` como parametro opcional en lugar de obtenerlo internamente via `logging.getLogger()`
- `build_filepath()` en `storage.py` ahora crea automaticamente la carpeta de salida con `os.makedirs(exist_ok=True)` si no existe

### Architecture
- `utils.py` como punto de extension natural: el data engineer agrega helpers de extraccion ahi sin tocar el flujo principal de `scraper.py`
- Consistencia en el paso de `logger`: todos los modulos del job (`scraper.py`, `process.py`) lo reciben como parametro

## [0.12.0] - 2026-03-12

### Added
- Soporte para **multiples procesos de scraping** mediante arquitectura multi-job
- Carpeta `src/shared/` con modulos reutilizables entre todos los jobs: `storage.py`, `driver_config.py`, `logger.py`
- Carpeta `src/viviendas_adonde/` como primer job concreto, con `scraper.py`, `process.py` y `app_job.py`
- Modulo `app_job.py` por proceso: encapsula el flujo ETL completo y expone `run(args)` como interfaz estandar
- Funcion `load_web_config()` movida de `main.py` a cada `app_job.py` con su ruta de config propia
- `config/global_settings.py` con configuracion compartida entre todos los jobs: `LOG_CONFIG` y `DATA_CONFIG`
- Carpeta `config/viviendas_adonde/` con `settings.py` (config especifica del job) y `web_config.yaml`
- Carpetas de salida por proceso: `output/viviendas_adonde/` y `raw/viviendas_adonde/`
- Tests globales en `tests/test_global.py`: `TestLogConfig` y `TestDataConfig`
- Tests por proceso en `tests/viviendas_adonde/test_config.py`: `TestWebConfig`, `TestStorageConfig`, `TestDriverConfig`, `TestRawConfig`

### Changed
- `main.py` refactorizado como **dispatcher dinamico**: carga el job indicado via `importlib` y llama `run(args)`
- CLI actualizado: argumento `--job` requerido para indicar el proceso a ejecutar
- `config/viviendas_adonde/settings.py` ahora solo contiene `DRIVER_CONFIG`, `STORAGE_CONFIG` y `RAW_CONFIG`
- `STORAGE_CONFIG["output_folder"]` actualizado a `output/viviendas_adonde`
- `RAW_CONFIG["raw_folder"]` actualizado a `raw/viviendas_adonde`
- Tests reorganizados en subdirectorios por proceso (espejo de la estructura `src/`)

### Removed
- `src/scraper.py`, `src/process.py`, `src/storage.py`, `src/driver_config.py`, `src/logger.py` — movidos a `src/shared/` o `src/viviendas_adonde/`
- `config/settings.py` y `config/web_config.yaml` — reemplazados por `config/global_settings.py` y `config/viviendas_adonde/`
- `tests/test_config.py` — reemplazado por `tests/test_global.py` y `tests/viviendas_adonde/test_config.py`

### Architecture
- Patron **multi-job dispatcher**: `main.py` es generico y delega en cada `app_job.py` segun `--job`
- Convencion de interfaz: todo job debe exponer `def run(args: argparse.Namespace) -> None` en su `app_job.py`
- Agregar un nuevo proceso = crear `src/<nombre>/app_job.py` + `config/<nombre>/` sin modificar `main.py`
- Tests siguen la misma estructura de carpetas que `src/` y `config/`

### CLI
```bash
python -m src.main --job viviendas_adonde
python -m src.main --job viviendas_adonde --reprocess 20260312_143052
```

## [0.11.0] - 2026-03-12

### Added
- Modulo `src/process.py` con funcion `process()` para transformacion de datos entre scraping y guardado final
- Funcion `save_raw()` en `storage.py`: guarda datos en bruto como CSV con sufijo timestamp, retorna el sufijo generado
- Funcion `cleanup_raw()` en `storage.py`: aplica politica de retencion sobre la carpeta `raw/`
- Configuracion `RAW_CONFIG` en `config/settings.py` con `raw_folder`, `filename`, `format` y `retention`
- Soporte CLI con `argparse`: flag `--reprocess <SUFFIX>` para reprocesar un raw existente sin volver a scrapear
- Carpeta `raw/` para almacenar archivos intermedios
- Clase `TestRawConfig` en `tests/test_config.py` con 4 tests de validacion

### Changed
- `main.py` ampliado con dos flujos diferenciados:
  - **Flujo completo**: scraping → save_raw → process → cleanup_raw → save_data
  - **Flujo reprocess** (`--reprocess SUFFIX`): process → save_data
- `main.py` libera memoria (`del datos`) entre save_raw y process para soportar datasets grandes

### Architecture
- Pipeline de datos en tres etapas: raw (CSV) → process (list[dict]) → output (formatos configurados)
- `process()` recibe `filename`, `extension` y `suffix`; resuelve el path internamente desde `raw_config`
- El sufijo timestamp es el identificador unico de cada ejecucion de scraping

## [0.10.0] - 2026-03-09

### Added
- Campo `output_formats` en `STORAGE_CONFIG` para configurar formatos de salida
- Soporte para exportar a multiples formatos simultaneamente
- Type hints en todos los modulos: `main.py`, `scraper.py`, `storage.py`, `driver_config.py`, `logger.py`

### Changed
- `main.py` ahora itera sobre `output_formats` para exportar a todos los formatos configurados
- Formato de salida ya no esta hardcodeado, es configurable via `STORAGE_CONFIG`

## [0.9.0] - 2026-03-09

### Added
- Modulo `src/scraper.py` con funcion `scrape()` para logica de extraccion
- Modulo `src/storage.py` con funciones `save_data()` y `build_filepath()`
- Seccion "Arquitectura" en README con diagrama de flujo
- Seccion "API Reference" en README con documentacion de funciones publicas

### Changed
- Refactorizacion de `main.py` aplicando Single Responsibility Principle
- `main.py` reducido de 177 a 39 lineas (solo orquestacion)
- `load_web_config()` ahora tiene logger como parametro opcional (compatibilidad con tests)
- README actualizado con nueva estructura de archivos

### Architecture
- Separacion de responsabilidades en 3 modulos:
  - `main.py`: Orquestacion del flujo
  - `scraper.py`: Logica de extraccion de datos
  - `storage.py`: Persistencia y exportacion

## [0.8.0] - 2026-02-03

### Added
- Sistema de logging con salida dual (archivo + consola)
- Modulo `src/logger.py` con funcion `setup_logger()`
- Configuracion `LOG_CONFIG` en `config/settings.py`
- Carpeta `log/` para almacenar archivos de log
- Logs nombrados por fecha: `scrapecraft_YYYYMMDD.log`
- Logging en puntos clave: inicio, carga config, driver, scraping, guardado, fin
- Manejo de errores con traceback en logs

### Changed
- Proyecto renombrado a **ScrapeCraft**
- `print()` reemplazado por `logger.info()` / `logger.error()` en todo el proyecto
- `load_web_config()` ahora recibe logger como parametro
- `scrape()` ahora recibe logger como parametro
- README actualizado con nuevo nombre, seccion de proposito y aviso legal

### Updated
- `.gitignore` ahora ignora archivos `.log` pero mantiene `log/.gitkeep`

## [0.7.0] - 2026-01-30

### Changed
- `DATA_CONFIG` reestructurado como diccionario anidado con configuraciones independientes por formato
- Cada formato (csv, json, xml, xlsx) tiene su propia configuracion separada
- Funcion `save_data()` ahora recibe `format` como parametro independiente
- Funcion `build_filepath()` ahora recibe `format` como parametro en lugar de `data_config`

### Added
- Soporte para formato Excel (`xlsx`) con opciones `sheet_name` e `index`
- Nuevas opciones para CSV: `separator`, `index`
- Nuevas opciones para JSON: `orient`, `force_ascii`

### Tests
- Simplificado `TestDataConfig` a un solo test que valida existencia y al menos un formato
- Total de tests: 12 (antes 14)

### Removed
- Campo `format` de nivel superior en DATA_CONFIG (ahora el formato se pasa como parametro)

## [0.6.0] - 2026-01-30

### Added
- Nueva configuracion `DATA_CONFIG` para formato de datos (csv_encoding, json_indent, xml_root, xml_row)
- Nueva configuracion `STORAGE_CONFIG` para almacenamiento (output_folder, filename, naming_mode)
- Funcion `build_filepath()` en `main.py` para construir rutas segun modo de nombrado
- Soporte para 4 modos de nombrado de archivos:
  - `overwrite`: Sobrescribe el archivo existente (viviendas.csv)
  - `date_suffix`: Añade fecha al nombre (viviendas_20260130.csv)
  - `timestamp_suffix`: Añade fecha y hora (viviendas_20260130_143052.csv)
  - `date_folder`: Crea subcarpeta con fecha (20260130/viviendas.csv)

### Changed
- `OUTPUT_CONFIG` separado en `DATA_CONFIG` y `STORAGE_CONFIG` para mejor organizacion
- Funcion `save_data()` ahora recibe `data_config` y `storage_config` como argumentos separados
- Carpeta de salida ahora es configurable via `STORAGE_CONFIG["output_folder"]`

### Removed
- `OUTPUT_CONFIG` reemplazado por las nuevas configuraciones separadas

### Tests
- Clase `TestDataConfig` con 3 tests para validar DATA_CONFIG
- Clase `TestStorageConfig` con 4 tests para validar STORAGE_CONFIG
- Total de tests: 14 (antes 7)

## [0.5.0] - 2026-01-24

### Added
- Carpeta `src/` para codigo fuente
- Carpeta `config/` para archivos de configuracion
- Carpeta `tests/` para tests
- Carpeta `output/` para archivos generados
- Archivos `__init__.py` en cada paquete
- Archivo `.gitkeep` en `output/`

### Changed
- Reorganizacion del proyecto siguiendo estandar Python (src layout)
- `config.py` renombrado a `config/settings.py`
- `web_config.yaml` movido a `config/`
- `main.py` y `driver_config.py` movidos a `src/`
- `test_driver_config.py` movido a `tests/test_config.py`
- Archivos de salida ahora se guardan en `output/`
- Actualizados imports en todos los modulos

## [0.4.0] - 2026-01-24

### Added
- Archivo `requirements.txt` con dependencias del proyecto
- Clase `TestWebConfig` con validaciones:
  - `test_web_config_file_exists`: Verifica existencia del YAML
  - `test_web_config_has_required_keys`: Valida claves requeridas
  - `test_url_format_is_valid`: Valida formato de URL (http/https + dominio)
  - `test_xpath_selectors_format`: Valida formato XPath (/, // o .//)
  - `test_waits_are_positive_numbers`: Valida que waits sean numeros positivos

## [0.3.0] - 2026-01-24

### Added
- Archivo `web_config.yaml` para configuracion de la web a scrapear
- Funcion `load_web_config()` en `main.py` para cargar configuracion YAML
- Dependencia de `pyyaml` para parsing de archivos YAML

### Changed
- `scrape()` ahora recibe `web_config` en lugar de `url`, usa selectores del YAML
- Selectores XPath externalizados a `web_config.yaml` (url, xpath_selectors, waits)
- La extraccion de campos es dinamica: itera sobre los selectores definidos en el YAML

## [0.2.0] - 2026-01-24

### Added
- Funcion `scrape(driver, url)` en `main.py` para encapsular la logica de extraccion
- Funcion `save_data(datos, output_config)` en `main.py` para guardar datos en multiples formatos
- Soporte para exportar a CSV, JSON y XML usando pandas
- Seccion `OUTPUT_CONFIG` en `config.py` con opciones:
  - `format`: Formato de salida (csv/json/xml)
  - `filename`: Nombre del archivo sin extension
  - `csv_encoding`: Encoding para CSV
  - `json_indent`: Indentacion para JSON
  - `xml_root` / `xml_row`: Nombres de elementos XML

### Changed
- Refactorizado `main.py` con estructura modular: `scrape()`, `save_data()`, `main()`
- `main()` ahora usa `try/finally` para asegurar cierre del driver
- Agregado `if __name__ == "__main__":` para ejecucion como script

### Removed
- Import no utilizado de `selenium.webdriver`
- Comentarios redundantes en `main.py`

## [0.1.0] - 2026-01-23

### Added
- Estructura inicial del proyecto
- `config.py` con `DRIVER_CONFIG` para configuracion centralizada del driver
- `driver_config.py` con clase `DriverConfig` para inicializar SeleniumBase
- `main.py` con script de scraping basico
- `test_driver_config.py` con tests para verificar inicializacion del driver
- Soporte para opciones: headless, undetected, maximize, window_size, user_agent, proxy
