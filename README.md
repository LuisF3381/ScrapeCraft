# ScrapeCraft

Plantilla open source para construir web scrapers de forma facil y rapida. Basada en [SeleniumBase](https://github.com/seleniumbase/SeleniumBase), un framework de automatizacion con soporte integrado para evasion de deteccion.

## Proposito

ScrapeCraft busca ser un punto de partida para cualquier persona que quiera aprender web scraping o construir sus propios scrapers para **fines educativos y divertidos**. La plantilla esta disenada para ser:

- **Facil de usar**: Configura tu scraper editando archivos YAML y Python, sin tocar el codigo principal
- **Flexible**: Soporta multiples procesos de scraping y multiples formatos de salida (CSV, JSON, XML, Excel)
- **Robusta**: Incluye sistema de logging, manejo de errores y evasion de deteccion

## Estructura

```
ScrapeCraft/
├── src/
│   ├── main.py                        # Dispatcher: lanza el job indicado por CLI
│   ├── shared/                        # Modulos reutilizables entre todos los jobs
│   │   ├── driver_config.py           # Inicializacion del driver (create_driver)
│   │   ├── job_runner.py              # Orquestacion ETL generica
│   │   ├── logger.py                  # Sistema de logging
│   │   ├── storage.py                 # Almacenamiento y exportacion
│   │   └── utils.py                   # Funciones auxiliares de extraccion
│   ├── viviendas_adonde/              # Job: portal de alquiler de inmuebles
│   │   ├── settings.py                # Config del job: DRIVER, STORAGE, RAW, SKIP_PROCESS
│   │   ├── web_config.yaml            # URL, selectores XPath y waits
│   │   ├── scraper.py
│   │   ├── process.py
│   │   ├── utils.py
│   │   └── app_job.py
│   └── books_to_scrape/               # Job: catalogo de libros (sitio de practica)
│       ├── settings.py
│       ├── web_config.yaml
│       ├── scraper.py
│       ├── process.py
│       ├── utils.py
│       └── app_job.py
├── config/
│   ├── global_settings.py             # Config global: LOG_CONFIG, DATA_CONFIG
│   └── pipelines/
│       └── diario.yaml                # Ejemplo de pipeline multi-job
├── .state/                            # Estado de ejecucion (gitignored)
│   ├── books_to_scrape_params.json    # Params persistidos del ultimo run
│   └── viviendas_adonde_params.json
├── tests/
│   ├── test_global.py                 # Tests de configuracion global
│   ├── viviendas_adonde/
│   │   └── test_viviendas_adonde.py
│   └── books_to_scrape/
│       └── test_books_to_scrape.py
├── log/                               # Logs de ejecucion (compartido)
├── output/
│   ├── viviendas_adonde/
│   └── books_to_scrape/
├── raw/
│   ├── viviendas_adonde/
│   └── books_to_scrape/
├── requirements.txt
├── CHANGELOG.md
└── LICENSE
```

## Arquitectura

El proyecto sigue un patron **multi-job dispatcher**:

```
main.py (Dispatcher CLI)
    │
    └── importlib → src.<job>.app_job.run(args)
                        │
                        └── shared/job_runner.run()     # Orquestacion ETL generica
                                │
                                ├── load_web_config()   # Carga src/<job>/web_config.yaml
                                │
                                ├── shared/driver_config.py
                                │   └── DriverConfig    # Inicializa el browser
                                │
                                ├── scraper.py
                                │   └── scrape()        # Extrae datos de la web
                                │
                                ├── shared/storage.py
                                │   ├── save_raw()      # Guarda raw en raw/<job>/
                                │   ├── cleanup_raw()   # Aplica politica de retencion
                                │   └── save_data()     # Exporta a output/<job>/
                                │
                                └── process.py
                                    └── process()       # Transforma raw → procesado
```

### Modulos compartidos (`src/shared/`)

| Modulo | Responsabilidad |
|--------|-----------------|
| `job_runner.py` | Orquestacion ETL generica: `_run_full`, `_run_reprocess`, `_save_output`, `run` |
| `storage.py` | Persistencia: raw, cleanup, construir rutas, exportar en multiples formatos |
| `driver_config.py` | `create_driver(config)`: inicializa el navegador con opciones anti-deteccion |
| `logger.py` | Sistema de logging dual (archivo + consola) |
| `utils.py` | Funciones auxiliares de extraccion reutilizables: `safe_get_text`, `safe_get_attr` |

### Modulos por job (`src/<job>/`)

| Modulo | Responsabilidad |
|--------|-----------------|
| `app_job.py` | Declara los imports del job (`scraper`, `process`, `settings`) y delega en `job_runner.run()` |
| `scraper.py` | Logica de extraccion: navegar, manejar CAPTCHA, extraer elementos |
| `process.py` | Transformacion de datos entre el raw y el guardado final |
| `utils.py` | `parse_record()` con logica especifica del job; importa `safe_get_text`/`safe_get_attr` de shared |

## Instalacion

```bash
git clone https://github.com/tu-usuario/ScrapeCraft.git
cd ScrapeCraft
pip install -r requirements.txt
```

## Uso

```bash
# Ver los jobs disponibles
python -m src.main --list

# --- Job individual ---
python -m src.main --job viviendas_adonde
python -m src.main --job books_to_scrape --params "categoria=mystery&pagina=2"
python -m src.main --job books_to_scrape --reprocess 20260313_142546

# --- Ejecucion en serie ---
python -m src.main --jobs books_to_scrape,viviendas_adonde   # subset especifico
python -m src.main --all                                      # todos los jobs
python -m src.main --pipeline config/pipelines/diario.yaml   # pipeline con params por job

# --- Tests ---
pytest tests/ -v
pytest tests/test_global.py -v
pytest tests/books_to_scrape/ -v
pytest tests/viviendas_adonde/ -v
```

## Ejecucion en serie

ScrapeCraft soporta cuatro modos de ejecucion que son mutuamente excluyentes:

| Modo | Comando | Params |
|------|---------|--------|
| Job individual | `--job nombre` | `--params` o `.state/<job>_params.json` |
| Subset especifico | `--jobs job1,job2,...` | `.state/<job>_params.json` de cada job |
| Todos los jobs | `--all` | `.state/<job>_params.json` de cada job |
| Pipeline YAML | `--pipeline ruta.yaml` | Campo `params` del YAML |

`--reprocess` y `--params` solo son compatibles con `--job`. En modos de serie, cada job resuelve sus params automaticamente desde su archivo en `.state/`.

### Pipeline YAML

Permite definir pipelines nombrados y reutilizables con params independientes por job:

```yaml
# config/pipelines/diario.yaml
jobs:
  - name: books_to_scrape
    params: "categoria=mystery&pagina=1"   # opcional

  - name: viviendas_adonde
    params: "pais=peru"
```

```bash
python -m src.main --pipeline config/pipelines/diario.yaml
```

Los params del YAML se pasan al scraper de cada job y se persisten en `.state/<job>_params.json`. Si un job no tiene `params` en el YAML, carga su archivo de params en `.state/` como en modo normal.

### Comportamiento ante fallos en serie

Si un job falla, el error se registra y la ejecucion continua con el siguiente. Al finalizar se muestra un resumen:

```
==================================================
Serie finalizada: 2/2 jobs exitosos
```

o en caso de error parcial:

```
==================================================
Serie finalizada: 1/2 jobs exitosos
Jobs con error: viviendas_adonde
```

### Flujo completo (`skip_process=False`)

```
scrape() → save_raw() → del datos → process() → cleanup_raw() → save_data()
```

1. Extrae datos de la web y los guarda en `raw/<job>/` como CSV con sufijo timestamp
2. Libera la memoria del raw y aplica las transformaciones definidas en `process.py`
3. Limpia archivos antiguos de `raw/<job>/` segun la politica de retencion configurada
4. Guarda el resultado final en `output/<job>/` en los formatos configurados

### Flujo sin procesamiento (`skip_process=True`)

```
scrape() → save_raw() → del datos → cleanup_raw() → save_data()
```

Util cuando la web ya devuelve datos normalizados y no se requiere transformacion. Se activa con `SKIP_PROCESS = True` en `settings.py`.

### Parametros para el scraper (`--params`)

Permite pasar valores dinamicos al scraper sin tocar el codigo ni la configuracion:

```bash
python -m src.main --job viviendas_adonde --params "fecha=01/12/2024&pais=peru"
```

El string se parsea a un dict y llega al scraper como el argumento `params`:

```python
def scrape(driver, web_config, params):
    fecha = params.get("fecha")   # "01/12/2024"
    pais  = params.get("pais")    # "peru"
    # Usar para construir la URL, filtrar elementos, ajustar selectores, etc.
```

**Reglas del formato:**
- Separador de pares: `&`
- Separador de clave y valor: `=`
- `&` y `=` son caracteres reservados y no pueden aparecer en los valores
- Todos los valores llegan como `str` — convierte el tipo dentro del scraper si es necesario
- En modo `--reprocess` los params se ignoran (el scraper no se ejecuta)

**Persistencia de params entre ejecuciones:**

Cada vez que se pasa `--params`, el sistema los guarda en `.state/<job>_params.json`. Si en la siguiente ejecucion no se pasa `--params`, se cargan automaticamente los de la ultima vez:

```bash
# Define y guarda los params
python -m src.main --job viviendas_adonde --params "fecha=01/12/2024&pais=peru"

# Las siguientes ejecuciones los recuerdan sin escribirlos
python -m src.main --job viviendas_adonde
python -m src.main --job viviendas_adonde

# Para cambiarlos, vuelve a pasar --params
python -m src.main --job viviendas_adonde --params "fecha=15/12/2024&pais=argentina"
```

Cada job tiene su propio archivo de params independiente en `.state/`. El directorio esta en `.gitignore` — los params no se versionan.

### Reprocesamiento

Cuando necesitas volver a aplicar `process.py` sobre datos ya scrapeados (por ejemplo, tras corregir la logica de transformacion) sin lanzar el navegador:

```bash
python -m src.main --job viviendas_adonde --reprocess 20260312_143052
```

El sufijo identifica la ejecucion y corresponde al timestamp del archivo en `raw/<job>/`:

```
raw/viviendas_adonde/
└── viviendas_20260312_143052.csv   ← sufijo: 20260312_143052
```

## Configuracion

### Global (`config/global_settings.py`)

Aplica a todos los jobs. Contiene `LOG_CONFIG` y `DATA_CONFIG`.

```python
LOG_CONFIG = {
    "log_folder": "log",    # Carpeta de logs (compartida entre todos los jobs)
    "level": "INFO"         # Nivel: DEBUG, INFO, WARNING, ERROR
}
```

Cada ejecucion genera su propio archivo de log: `log/<job>_YYYYMMDD_HHMMSS.log`. El timestamp completo garantiza que multiples ejecuciones del mismo dia no mezclen sus logs.

```python
DATA_CONFIG = {
    "csv":  {"encoding": "utf-8", "separator": ";", "index": False},
    "json": {"indent": 2, "force_ascii": False, "orient": "records"},
    "xml":  {"root": "registros", "row": "registro"},
    "xlsx": {"sheet_name": "Datos", "index": False}
}
```

`DATA_CONFIG` es la unica fuente de verdad para los parametros de cada formato. Se aplica tanto al output final (`save_data`) como al raw intermedio (`save_raw`, `load_raw`, `process.py`).

### Por job (`src/<job>/settings.py`)

Especifica del job. Contiene `DRIVER_CONFIG`, `STORAGE_CONFIG`, `RAW_CONFIG` y `SKIP_PROCESS`.

```python
DRIVER_CONFIG = {
    "headless": False,      # Ejecutar sin interfaz grafica
    "undetected": True,     # Modo anti-deteccion
    "maximize": True,       # Maximizar ventana
    "window_size": None,    # Tamano especifico: (1920, 1080)
    "user_agent": None,     # User agent personalizado
    "proxy": None           # Proxy: "ip:puerto"
}

STORAGE_CONFIG = {
    "output_folder": "output/viviendas_adonde",
    "filename": "viviendas",
    "naming_mode": "date_suffix",    # overwrite | date_suffix | timestamp_suffix | date_folder
    "output_formats": ["csv", "json"]
}

RAW_CONFIG = {
    "raw_folder": "raw/viviendas_adonde",
    "filename": "viviendas",
    "format": "csv",             # csv | json | xml | xlsx
    "retention": {
        "mode": "keep_last_n",  # keep_all | keep_last_n | keep_days
        "value": 5
    }
}

SKIP_PROCESS = False   # True: omite process.py y guarda el raw directamente
```

#### Modos de nombrado (`naming_mode`)

| Modo | Resultado | Uso |
|------|-----------|-----|
| `overwrite` | `output/<job>/viviendas.csv` | Sobrescribe siempre |
| `date_suffix` | `output/<job>/viviendas_20260130.csv` | Una ejecucion por dia |
| `timestamp_suffix` | `output/<job>/viviendas_20260130_143052.csv` | Multiples ejecuciones por dia |
| `date_folder` | `output/<job>/20260130/viviendas.csv` | Organizar por carpetas |

#### Formato de raw (`format`)

El campo `format` determina en que formato se persiste el raw intermedio. El pipeline usa automaticamente la configuracion de `DATA_CONFIG[format]` para leer y escribir.

| Formato | Config aplicada | Archivo generado |
|---------|-----------------|------------------|
| `csv`  | `DATA_CONFIG["csv"]`  | `viviendas_20260312_143052.csv`  |
| `json` | `DATA_CONFIG["json"]` | `viviendas_20260312_143052.json` |
| `xml`  | `DATA_CONFIG["xml"]`  | `viviendas_20260312_143052.xml`  |
| `xlsx` | `DATA_CONFIG["xlsx"]` | `viviendas_20260312_143052.xlsx` |

#### Politicas de retencion de raw

| Modo | Comportamiento |
|------|----------------|
| `keep_all` | Conserva todos los archivos raw |
| `keep_last_n` | Conserva los ultimos N archivos, ordenados por timestamp en el nombre |
| `keep_days` | Conserva los archivos cuyo timestamp en el nombre no supere N dias de antiguedad |

### Web (`src/<job>/web_config.yaml`)

```yaml
url: "https://ejemplo.com"

xpath_selectors:
  container: '//div[@class="item"]'
  Campo1: './/span[@class="dato1"]'
  Campo2: './/span[@class="dato2"]'

waits:
  reconnect_attempts: 3
  after_load: 5
```

## Agregar un nuevo proceso

1. Crear `src/<nombre>/app_job.py` con las tres importaciones del job y la llamada al runner:

```python
from pathlib import Path
from src.<nombre>.scraper import scrape
from src.<nombre>.process import process
from src.<nombre> import settings
from src.shared.job_runner import run as _run_job

_JOB_NAME = Path(__file__).parent.name

def run(args):
    _run_job(args, scrape, process, settings, _JOB_NAME)
```

2. Crear `src/<nombre>/scraper.py` con la logica de extraccion
3. Crear `src/<nombre>/utils.py` con `parse_record()` (importa `safe_get_text`/`safe_get_attr` desde `src.shared.utils`)
4. Crear `src/<nombre>/process.py` con la logica de transformacion
5. Crear `src/<nombre>/settings.py` con `DRIVER_CONFIG`, `STORAGE_CONFIG`, `RAW_CONFIG` y `SKIP_PROCESS`
6. Crear `src/<nombre>/web_config.yaml` con la URL y los selectores

Las carpetas `output/<nombre>/` y `raw/<nombre>/` se crean automaticamente en la primera ejecucion. No es necesario modificar `main.py` ni ningun otro modulo del framework.

Luego ejecutar:

```bash
python -m src.main --job <nombre>
```

No es necesario modificar `main.py`.

## Procesamiento (`src/<job>/process.py`)

Implementa tu logica de transformacion dentro de `process()`. Recibe un DataFrame con todas las columnas como `str` — convierte los tipos que necesites explicitamente:

```python
def process(df: pd.DataFrame) -> list[dict]:
    # todas las columnas llegan como str (lineamiento string-first)

    # --- Tu logica aqui ---
    # Convierte tipos donde sea necesario, por ejemplo:
    # df["precio"] = df["precio"].str.replace(r"[^\d]", "", regex=True).astype(int)

    return df.to_dict(orient="records")
```

`app_job.py` se encarga de cargar el raw y construir el DataFrame antes de llamar a `process()`. El modulo no tiene dependencias de I/O — solo recibe datos y devuelve datos.

### Lineamiento string-first

El raw intermedio se persiste siempre como `str`. El output final preserva los tipos que `process.py` asigne:

- **Al escribir raw** (`save_raw`): se aplica `df.fillna("").astype(str)` — los `NaN` reales se rellenan con `""` antes de convertir a string, preservando el literal `"nan"` como dato valido en campos de texto
- **Al leer** (`load_raw`): se usa `dtype=str` para evitar inferencia de tipos — todas las columnas llegan a `process()` como `str`
- **Al escribir output** (`save_data`): se preservan los tipos que `process.py` asigno (`float`, `int`, `datetime`, etc.) — en JSON los numeros se guardan como numeros, en XLSX las celdas mantienen su tipo

Esto garantiza que valores como `"001"`, `"N/A"`, `"1.500,00"` o registros danados se preserven exactamente como llegan del scraper. La conversion de tipos es responsabilidad exclusiva de `process.py`.

## API Reference

### `src/shared/job_runner.py`

```python
def load_web_config(job_name: str) -> dict:
    """Carga la configuracion de la web desde src/<job_name>/web_config.yaml."""

def run(args, scrape_fn, process_fn, settings, job_name: str) -> None:
    """
    Punto de entrada generico para cualquier job. Llamado desde app_job.run().

    Flujo completo:    scrape → save_raw → load_raw → process(df) → cleanup_raw → save_data
    Sin proceso:       scrape → save_raw → load_raw → cleanup_raw → save_data
    Flujo reprocess:   load_raw → process(df) → save_data
    """
```

### `src/shared/storage.py`

```python
def save_data(datos, format, data_config, storage_config, now=None) -> None:
    """Guarda los datos en el formato y ubicacion especificados preservando los tipos de cada campo.
    now: datetime opcional; si se omite se usa datetime.now(). Pasar el mismo valor que a save_raw()
    garantiza timestamps coherentes entre el raw y el output de una misma ejecucion."""

def save_raw(datos, raw_config, data_config, now=None) -> str:
    """Guarda datos en bruto en el formato de raw_config["format"]. Retorna el sufijo timestamp.
    now: datetime opcional; si se omite se usa datetime.now(). Pasar el mismo valor que a save_data()
    garantiza coherencia de timestamps entre raw y output."""

def load_raw(suffix, raw_config, data_config) -> list[dict]:
    """Lee un raw existente y lo retorna como lista de dicts sin transformar. Lee todo como str."""

def cleanup_raw(raw_config) -> None:
    """Limpia archivos raw segun la politica de retencion configurada."""

def build_filepath(storage_config, format, now=None) -> Path:
    """Construye la ruta del archivo segun el modo de nombrado configurado.
    now: datetime opcional; si se omite se usa datetime.now()."""
```

### `src/shared/utils.py`

```python
def safe_get_text(element, xpath, fallback="") -> str:
    """Extrae el texto de un sub-elemento. Retorna fallback si no existe."""

def safe_get_attr(element, xpath, attr, fallback="") -> str:
    """Extrae el valor de un atributo HTML de un sub-elemento. Retorna fallback si no existe.
    Util cuando el dato esta en un atributo (ej: @title, @class, @href) en lugar del texto."""
```

### `src/<job>/scraper.py`

```python
def scrape(driver, web_config, params: dict = None) -> list[dict]:
    """
    Extrae datos desde la URL usando los selectores del archivo de configuracion.
    params: dict con los parametros pasados via --params en CLI (vacio si no se paso ninguno).
    Los valores son siempre str — convierte tipos dentro del scraper si es necesario.
    """
```

### `src/<job>/process.py`

```python
def process(df: pd.DataFrame) -> list[dict]:
    """Recibe un DataFrame con columnas en str y aplica transformaciones y castings de tipo."""
```

### `src/<job>/utils.py`

```python
def parse_record(item, selectors, index) -> dict:
    """Construye el diccionario de un registro a partir de un elemento contenedor.
    Implementa la logica especifica del job para cada campo (texto, atributo, etc.).
    Importa safe_get_text y safe_get_attr desde src.shared.utils."""
```

### `src/<job>/app_job.py`

```python
def run(args: argparse.Namespace) -> None:
    """Punto de entrada del job. Interfaz estandar requerida por el dispatcher.
    Declara los imports del job y delega en job_runner.run()."""
```

## Tests

### `tests/test_global.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestLogConfig` | `test_global_settings_has_log_config` | Verifica que LOG_CONFIG existe |
| `TestLogConfig` | `test_log_config_has_required_keys` | Valida claves requeridas |
| `TestLogConfig` | `test_log_config_level_is_valid` | Valida nivel de logging |
| `TestDataConfig` | `test_global_settings_has_data_config` | Verifica DATA_CONFIG con al menos un formato |
| `TestDataConfig` | `test_data_config_formats_have_required_keys` | Valida que cada formato tiene configuracion |

### `tests/viviendas_adonde/test_viviendas_adonde.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestWebConfig` | `test_web_config_file_exists` | Verifica existencia del YAML |
| `TestWebConfig` | `test_web_config_has_required_keys` | Valida claves requeridas |
| `TestWebConfig` | `test_url_format_is_valid` | Valida formato URL |
| `TestWebConfig` | `test_xpath_selectors_format` | Valida formato XPath |
| `TestWebConfig` | `test_waits_are_positive_numbers` | Valida waits numericos |
| `TestStorageConfig` | `test_settings_has_storage_config` | Verifica STORAGE_CONFIG existe |
| `TestStorageConfig` | `test_storage_config_has_required_keys` | Valida claves requeridas |
| `TestStorageConfig` | `test_storage_config_naming_mode_is_valid` | Valida naming_mode |
| `TestStorageConfig` | `test_storage_config_output_folder_is_valid_path` | Verifica que output_folder es una cadena no vacia |
| `TestDriverConfig` | `test_settings_file_has_driver_config` | Verifica DRIVER_CONFIG existe |
| `TestDriverConfig` | `test_driver_instance_created_with_settings_file` | Test de instancia del driver |
| `TestRawConfig` | `test_settings_has_raw_config` | Verifica RAW_CONFIG existe |
| `TestRawConfig` | `test_raw_config_has_required_keys` | Valida claves requeridas |
| `TestRawConfig` | `test_raw_config_format_is_valid` | Verifica que el formato raw es uno de los soportados |
| `TestRawConfig` | `test_raw_config_retention_mode_is_valid` | Valida modo de retencion |

### `tests/books_to_scrape/test_books_to_scrape.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestWebConfig` | `test_web_config_file_exists` | Verifica existencia del YAML |
| `TestWebConfig` | `test_web_config_has_required_keys` | Valida claves requeridas |
| `TestWebConfig` | `test_url_format_is_valid` | Valida formato URL |
| `TestWebConfig` | `test_xpath_selectors_has_container` | Verifica selector container obligatorio |
| `TestWebConfig` | `test_xpath_selectors_format` | Valida formato XPath de todos los selectores |
| `TestWebConfig` | `test_xpath_selectors_has_expected_fields` | Verifica campos Titulo, Precio y Rating |
| `TestWebConfig` | `test_waits_are_positive_numbers` | Valida waits numericos |
| `TestStorageConfig` | `test_settings_has_storage_config` | Verifica STORAGE_CONFIG existe |
| `TestStorageConfig` | `test_storage_config_has_required_keys` | Valida claves requeridas |
| `TestStorageConfig` | `test_storage_config_naming_mode_is_valid` | Valida naming_mode |
| `TestStorageConfig` | `test_storage_config_output_folder_is_valid_path` | Verifica que output_folder es una cadena no vacia |
| `TestStorageConfig` | `test_storage_config_output_formats_are_valid` | Valida formatos de salida |
| `TestDriverConfig` | `test_settings_file_has_driver_config` | Verifica DRIVER_CONFIG existe |
| `TestDriverConfig` | `test_driver_instance_created_with_settings_file` | Test de instancia del driver |
| `TestRawConfig` | `test_settings_has_raw_config` | Verifica RAW_CONFIG existe |
| `TestRawConfig` | `test_raw_config_has_required_keys` | Valida claves requeridas |
| `TestRawConfig` | `test_raw_config_format_is_valid` | Verifica que el formato raw es uno de los soportados |
| `TestRawConfig` | `test_raw_config_retention_mode_is_valid` | Valida modo de retencion |
| `TestProcess` | `test_process_returns_list_of_dicts` | Verifica el tipo de retorno |
| `TestProcess` | `test_process_precio_gbp_conversion` | Valida conversion de "£51.77" a 51.77 |
| `TestProcess` | `test_process_rating_numerico_conversion` | Valida mapeo de "star-rating X" a entero 1-5 |
| `TestProcess` | `test_process_precio_empty_returns_none` | Precio vacio produce None en Precio_GBP |
| `TestProcess` | `test_process_preserves_all_records` | process() no descarta ni duplica registros |
| `TestUtils` | `test_safe_get_text_returns_text` | safe_get_text devuelve texto limpio |
| `TestUtils` | `test_safe_get_text_fallback_on_missing` | safe_get_text retorna fallback si no existe |
| `TestUtils` | `test_safe_get_attr_returns_attribute` | safe_get_attr devuelve el atributo HTML |
| `TestUtils` | `test_safe_get_attr_fallback_on_missing` | safe_get_attr retorna fallback si no existe |
| `TestUtils` | `test_parse_record_includes_numero` | parse_record incluye Numero y omite container |

## Requisitos

- Python 3.8+
- SeleniumBase
- pandas
- pyyaml
- pytest
- openpyxl

## Licencia

Este proyecto es open source y esta disponible bajo la [Licencia MIT](LICENSE).

## Aviso Legal

Esta plantilla esta destinada exclusivamente para fines educativos y de aprendizaje. Antes de realizar scraping en cualquier sitio web, asegurate de:

- Revisar y respetar los terminos de servicio del sitio
- Consultar el archivo `robots.txt`
- No sobrecargar los servidores con peticiones excesivas
- Respetar la privacidad y los datos personales

El uso responsable del web scraping es responsabilidad del usuario.
