# ScrapeCraft

Plantilla open source para construir web scrapers de forma facil y rapida. Basada en [SeleniumBase](https://github.com/seleniumbase/SeleniumBase), un framework de automatizacion con soporte integrado para evasion de deteccion.

## Proposito

ScrapeCraft busca ser un punto de partida para cualquier persona que quiera aprender web scraping o construir sus propios scrapers para **fines educativos y divertidos**. La plantilla esta disenada para ser:

- **Facil de usar**: Configura tu scraper editando archivos YAML y Python, sin tocar el codigo principal
- **Flexible**: Soporta multiples procesos de scraping y multiples formatos de salida (CSV, JSON, XML, Excel)
- **Robusta**: Incluye sistema de logging, manejo de errores y evasion de deteccion

> **Nuevo proyecto?** Usa el [ScrapeCraft Generator](../scrapecraft-generator/) para generar la estructura completa de tu proyecto de forma interactiva, sin copiar ni modificar esta plantilla manualmente.

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
│   ├── consolidadores/                # Modulos de consolidacion (uno por pipeline)
│   │   └── ejemplo.py                 # Consolidador de ejemplo
│   ├── viviendas_adonde/              # Job: portal de alquiler de inmuebles
│   │   ├── settings.py                # Config del job: DRIVER_CONFIG, STORAGE_CONFIG, SKIP_PROCESS
│   │   ├── web_config.yaml            # URL, selectores y waits
│   │   ├── scraper.py
│   │   ├── process.py
│   │   ├── validate.py                # Validaciones antes de guardar (gobierno de datos)
│   │   └── utils.py
│   └── books_to_scrape/               # Job: catalogo de libros (sitio de practica)
│       ├── settings.py
│       ├── web_config.yaml
│       ├── scraper.py
│       ├── process.py
│       ├── validate.py                # Validaciones antes de guardar (gobierno de datos)
│       └── utils.py
├── config/
│   ├── global_settings.py             # Config global: LOG_CONFIG
│   └── pipelines/
│       ├── diario.yaml                # Ejemplo de pipeline multi-job
│       └── diario_consolidado.yaml    # Ejemplo de pipeline con consolidacion
├── tests/
│   ├── test_global.py                 # Tests de configuracion global
│   ├── test_pipelines.py              # Tests de todos los pipelines (auto-discovery)
│   ├── viviendas_adonde/
│   │   └── test_viviendas_adonde.py
│   └── books_to_scrape/
│       └── test_books_to_scrape.py
├── run_history/                       # Historial de runs por job (JSON Lines, generado en ejecucion)
│   ├── books_to_scrape.jsonl
│   └── viviendas_adonde.jsonl
├── log/                               # Logs de ejecucion (compartido)
├── output/
│   ├── consolidados/                  # Output de consolidaciones
│   ├── viviendas_adonde/
│   └── books_to_scrape/
├── raw/
│   ├── viviendas_adonde/
│   └── books_to_scrape/
├── latest/                            # Espejo de la ultima ejecucion (rutas fijas para downstream)
│   ├── books_to_scrape/               #   generado por --job o --pipeline sin consolidar
│   │   ├── books.csv
│   │   ├── books.json
│   │   └── run.log
│   ├── viviendas_adonde/
│   │   ├── viviendas.csv
│   │   └── run.log
│   └── diario_consolidado/            #   generado por --pipeline con consolidar
│       ├── consolidado.csv
│       └── run.log                    #   logs de todos los jobs concatenados
├── requirements.txt
├── CHANGELOG.md
└── LICENSE
```

## Arquitectura

El proyecto sigue un patron **multi-job dispatcher**:

```
main.py (Dispatcher CLI)
    │
    └── importlib → src.<job>.{scraper, process, settings}
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
                                │   ├── save_raw()          # Guarda raw en raw/<job>/
                                │   ├── cleanup_raw()       # Aplica politica de retencion
                                │   ├── save_data()         # Exporta a output/<job>/
                                │   ├── clear_latest()      # Limpia latest/<job>/ antes de cada run
                                │   └── copy_to_latest()    # Copia output + log a latest/<job>/
                                │
                                ├── process.py
                                │   └── process()       # Transforma raw → procesado
                                │
                                └── validate.py
                                    └── validate()      # Valida antes de guardar (gobierno de datos)
```

### Modulos compartidos (`src/shared/`)

| Modulo | Responsabilidad |
|--------|-----------------|
| `job_runner.py` | Orquestacion ETL generica: `_run_full`, `_run_reprocess`, `_save_output`, `run`; registra el tiempo de cada etapa (`[scrape]`, `[process]`, `[validate]`, `[save]`) en el log |
| `storage.py` | Persistencia: raw, cleanup, construir rutas, exportar en multiples formatos con escritura atomica, cargar outputs para consolidacion, gestion de `latest/` |
| `driver_config.py` | `create_driver(config)`: inicializa el navegador con opciones anti-deteccion |
| `logger.py` | Sistema de logging dual (archivo + consola) con soporte thread-safe para ejecucion paralela; expone `get_current_log_path()` y `flush_log()` para la gestion de `latest/` |
| `run_history.py` | `record_run()`: registra el resultado de cada ejecucion en `run_history/<job>.jsonl`; permite auditar runs pasados, consultar el sufijo de un raw fallido y detectar jobs con fallos repetidos |
| `utils.py` | Funciones auxiliares de extraccion reutilizables: `safe_get_text`, `safe_get_attr` |

### Modulos consolidadores (`src/consolidadores/`)

| Modulo | Responsabilidad |
|--------|-----------------|
| `ejemplo.py` | Consolidador de ejemplo: combina todos los jobs por concatenacion con columna `_fuente` |

Cada consolidador define su propio `STORAGE_CONFIG` y una funcion `consolidate(job_dataframes, params)`. El framework gestiona el I/O — el consolidador solo implementa logica.

### Modulos por job (`src/<job>/`)

| Modulo | Responsabilidad |
|--------|-----------------|
| `scraper.py` | Logica de extraccion: navegar, manejar CAPTCHA, extraer elementos |
| `process.py` | Transformacion de datos entre el raw y el guardado final |
| `validate.py` | Validaciones de gobierno de datos antes de guardar; si falla, el output no se escribe |
| `utils.py` | `parse_record()` con logica especifica del job; importa `safe_get_text`/`safe_get_attr` de shared |

## Requisitos previos

- Python **3.10 o superior** (el codigo usa union types `X | Y` disponibles desde 3.10)
- Google Chrome instalado (SeleniumBase gestiona el chromedriver automaticamente)

## Instalacion

**1. Clonar o descargar el repositorio**

```bash
git clone <url-del-repositorio>
cd Plantilla-Scraping-SeleniumBase
```

**2. Crear y activar el entorno virtual**

```bash
# Crear
python -m venv venv

# Activar en Windows
venv\Scripts\activate

# Activar en macOS / Linux
source venv/bin/activate
```

**3. Instalar dependencias**

```bash
pip install -r requirements.txt
```

**4. Configurar variables de entorno (opcional)**

```bash
cp .env.example .env
# Editar .env con los valores necesarios (proxy, user agent, nivel de log)
```

El archivo `.env` nunca se commitea (esta en `.gitignore`). Si no lo creas, el proyecto funciona con los valores por defecto.

> Todos los comandos del proyecto deben ejecutarse desde la **raiz del repositorio** con el entorno virtual activo.

## Uso

```bash
# Ver los jobs disponibles
python -m src.main --list

# --- Job individual ---
python -m src.main --job books_to_scrape
python -m src.main --job viviendas_adonde

# --- Reprocesar raw existente sin volver a scrapear ---
python -m src.main --job books_to_scrape --reprocess 20260313_142546

# --- Ejecucion en serie (pipeline) ---
python -m src.main --pipeline config/pipelines/diario.yaml

# --- Ejecucion en serie con consolidacion ---
python -m src.main --pipeline config/pipelines/diario_consolidado.yaml

# --- Ejecucion en paralelo (requiere parallel: true en el YAML) ---
python -m src.main --pipeline config/pipelines/diario.yaml
```

## Tests

Los tests estan divididos en dos grupos segun si requieren o no un navegador:

**Tests de configuracion** — rapidos, sin browser:

```bash
# Todos los tests de configuracion y pipeline (recomendado para validacion rapida)
pytest tests/test_global.py tests/test_pipelines.py -v

# Solo configuracion global
pytest tests/test_global.py -v

# Solo pipelines
pytest tests/test_pipelines.py -v
```

**Tests de job** — incluyen un test que abre el browser en modo headless:

```bash
# Job books_to_scrape
pytest tests/books_to_scrape/ -v -s

# Job viviendas_adonde
pytest tests/viviendas_adonde/ -v -s

# Todos los tests (configuracion + todos los jobs)
pytest tests/ -v -s
```

> El test `test_driver_instance_created_with_settings_file` abre Chrome en modo headless para verificar que el driver se inicializa correctamente. Requiere Chrome instalado.

## Ejecucion de pipelines

ScrapeCraft tiene dos modos de ejecucion mutuamente excluyentes:

| Modo | Comando | Uso |
|------|---------|-----|
| Job individual | `--job nombre` | Un job, con `--reprocess` opcional |
| Pipeline YAML | `--pipeline ruta.yaml` | Uno o mas jobs con params, `enabled`, `schedule`, consolidacion y modo paralelo opcionales |

Para correr multiples jobs o pasar params, usa siempre `--pipeline`. El reprocesamiento (`--reprocess`) es una operacion manual exclusiva de `--job`.

### Pipeline YAML

Permite definir pipelines nombrados y reutilizables con params independientes por job:

```yaml
# config/pipelines/diario.yaml
name: diario
description: "Scraping diario de catalogo y viviendas"   # opcional
# parallel: true   # Descomentar para lanzar todos los jobs a la vez

jobs:
  - name: books_to_scrape
    params:               # opcional, dict nativo YAML
      categoria: mystery
      pagina: 1           # llega como int, no como str

  - name: viviendas_adonde
    params:
      pais: peru
      max_paginas: 5
      solo_nuevos: true   # llega como bool

  # Desactivar un job sin borrarlo:
  # - name: otro_job
  #   enabled: false
```

```bash
python -m src.main --pipeline config/pipelines/diario.yaml
```

Los params se definen como dict YAML nativo — los tipos (`int`, `bool`, `float`, `str`) se preservan directamente en el scraper sin conversion manual.

### Schedule

Permite que cada job del pipeline declare en que dias debe ejecutarse. El pipeline se puede programar para correr diariamente (cron / Task Scheduler) y cada job decide por si solo si le corresponde correr ese dia.

```yaml
jobs:
  - name: reporte_mensual
    schedule:
      day_of_month: 3     # solo el dia 3 de cada mes

  - name: resumen_semanal
    schedule:
      day_of_week: 0      # solo los lunes (0=lunes ... 6=domingo)

  - name: scraping_diario
    # sin schedule = corre siempre
```

Los dos campos son combinables con AND logico — si se especifican ambos, el job solo corre si los dos coinciden a la vez.

Cuando un job es omitido por schedule el log indica:

```
[2/3] Job 'reporte_mensual' omitido: schedule={'day_of_month': 3}, hoy=01/04/2026
```

**Con consolidacion:** un job omitido por schedule **no bloquea** la consolidacion. El consolidador recibe `None` en lugar de un DataFrame para ese job y decide como manejarlo (ignorar la fuente, consolidar solo los presentes, etc.):

```python
def consolidate(job_dataframes: dict[str, pd.DataFrame | None], params=None):
    df_a = job_dataframes["job_a"]          # DataFrame o None
    df_b = job_dataframes["job_b"]          # DataFrame o None

    frames = [df for df in [df_a, df_b] if df is not None]
    if not frames:
        return []
    return pd.concat(frames, ignore_index=True).to_dict(orient="records")
```

Un job **fallido** (error inesperado) si bloquea la consolidacion — la distincion es intencional: un skip por schedule es planificado, un fallo no lo es.

### Ejecucion en paralelo

Agrega `parallel: true` al pipeline para lanzar todos los jobs al mismo tiempo. Util cuando los jobs son independientes entre si y quieres reducir el tiempo total de ejecucion.

```yaml
name: diario
parallel: true   # ← esto es todo

jobs:
  - name: books_to_scrape
  - name: viviendas_adonde
```

Con `consolidate` activo, los jobs corren en paralelo y la consolidacion siempre se ejecuta en serie al final, una vez que todos los jobs terminan. El comportamiento ante fallos es el mismo que en serie: si algun job falla, la consolidacion se omite.

Cada job escribe en su propio archivo de log. El logging es thread-safe — los logs nunca se mezclan entre archivos aunque los jobs compartan tiempo de CPU.

### Consolidacion

Un pipeline puede incluir un paso de consolidacion opcional que combina los outputs de todos los jobs en un unico dataset. Solo se ejecuta si **todos** los jobs del pipeline finalizaron exitosamente.

```yaml
# config/pipelines/diario_consolidado.yaml
name: diario_consolidado

jobs:
  - name: books_to_scrape
  - name: viviendas_adonde

consolidate:
  enabled: true
  module: ejemplo       # src/consolidadores/ejemplo.py
  format: csv           # todos los jobs deben incluir este formato en output_formats
  params: {}            # opcional, recibido en consolidate() como dict
```

```bash
python -m src.main --pipeline config/pipelines/diario_consolidado.yaml
```

El bloque `consolidate` requiere:
- `enabled` (bool): activa o desactiva la consolidacion
- `module` (str): nombre del modulo en `src/consolidadores/` (sin `.py`)
- `format` (str): formato compartido por todos los jobs (`csv`, `json`, `xml`, `xlsx`); todos deben incluirlo en su `output_formats`
- `params` (dict, opcional): parametros adicionales para la logica del consolidador

El framework valida estos requisitos **antes de lanzar cualquier job** — fallo rapido si algun job no cumple el formato requerido o si los jobs tienen `format_config` distintas para el formato compartido.

### Crear un consolidador

1. Crea `src/consolidadores/<nombre>.py` copiando `ejemplo.py`
2. Ajusta `STORAGE_CONFIG` (carpeta, nombre, naming_mode, formatos de salida)
3. Implementa `consolidate()` — el framework entrega los DataFrames listos, sin I/O

```python
# src/consolidadores/<nombre>.py
import pandas as pd

STORAGE_CONFIG = {
    "output_folder": "output/consolidados",
    "filename": "mi_consolidado",
    "naming_mode": "date_suffix",
    "output_formats": ["csv"],
    "format_config": {
        "csv": {"encoding": "utf-8", "separator": ";", "index": False},
        # Debe coincidir con la format_config de los jobs para el formato de consolidacion
    }
}

def consolidate(job_dataframes: dict[str, pd.DataFrame | None], params: dict = None) -> list[dict]:
    df_a = job_dataframes["job_a"]   # None si fue omitido por schedule ese dia
    df_b = job_dataframes["job_b"]
    # ... logica de combinacion (verificar None antes de usar cada df)
    return resultado.to_dict(orient="records")
```

El framework lee los outputs de cada job usando su propia `format_config` y entrega los DataFrames listos. El data engineer solo escribe logica.

Opcionalmente, el equipo de gobierno puede anadir una funcion `validate(df)` al consolidador siguiendo el mismo contrato que `src/<job>/validate.py`. Si esta presente, el framework la ejecuta despues de `consolidate()` y antes de guardar el output.

### Comportamiento ante fallos

Si un job falla, el error se registra y la ejecucion continua con el siguiente (serie) o termina ese hilo (paralelo). Al finalizar se muestra un resumen:

```
==================================================
Serie finalizada: 2/2 jobs exitosos
```

```
==================================================
Paralelo finalizado: 1/2 jobs exitosos
Jobs con error: viviendas_adonde
```

### Flujo completo (`skip_process=False`)

```
scrape() → save_raw() → normalize_in_memory() → process() → save_data() → cleanup_raw()
```

1. Extrae datos de la web y los guarda en `raw/<job>/` como CSV con sufijo timestamp
2. Normaliza el raw en memoria (`fillna("").astype(str)`) y aplica las transformaciones definidas en `process.py`
3. Guarda el resultado final en `output/<job>/` en los formatos configurados
4. Limpia archivos antiguos de `raw/<job>/` segun la politica de retencion configurada — siempre, tanto si el job finaliza exitosamente como si falla durante `process()`

### Flujo sin procesamiento (`skip_process=True`)

```
scrape() → save_raw() → normalize_in_memory() → save_data() → cleanup_raw()
```

Util cuando la web ya devuelve datos normalizados y no se requiere transformacion. Se activa con `SKIP_PROCESS = True` en `settings.py`.

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

## Latest — rutas fijas para procesos downstream

Cada ejecucion actualiza automaticamente la carpeta `latest/` con los archivos de la ultima ejecucion. Esto permite que cualquier proceso externo lea siempre desde una ruta fija sin depender del `naming_mode` ni del timestamp del run.

### Estructura

```
latest/
  <job_name>/              # --job o --pipeline sin consolidar
    <filename>.<ext>       # uno por cada formato en output_formats
    run.log                # log de esa ejecucion
  <pipeline_name>/         # --pipeline con consolidar
    <filename>.<ext>       # solo el output consolidado
    run.log                # logs de todos los jobs concatenados
```

### Comportamiento por modo

| Modo | Carpeta en latest/ | Exito | Fallo |
|------|--------------------|-------|-------|
| `--job` | `latest/<job>/` | output(s) + `run.log` | solo `run.log` |
| `--pipeline` sin consolidar | `latest/<job>/` por cada job | output(s) + `run.log` | solo `run.log` |
| `--pipeline` con consolidar | `latest/<pipeline_name>/` | output consolidado + `run.log` (logs concatenados) | solo `run.log` (logs concatenados) |
| `--reprocess` | `latest/<job>/` | output(s) + `run.log` | solo `run.log` |

**Reglas:**

- La carpeta `latest/<X>/` se borra y recrea al inicio de cada ejecucion — nunca quedan archivos de runs anteriores
- Si el job falla no se escribe ningun output en `latest/`, pero el log siempre se copia para mantener trazabilidad
- En pipelines con consolidacion los jobs individuales **no** escriben en `latest/` — solo escribe el consolidador al final
- En pipelines sin consolidacion cada job gestiona su propio `latest/<job>/` de forma independiente; el fallo de un job no afecta al `latest/` de los demas
- El `--reprocess` borra y actualiza unicamente `latest/<job>/` del job que se esta reprocesando

### Nombres de archivo en latest/

Los archivos en `latest/` usan siempre el nombre base configurado en `STORAGE_CONFIG["filename"]` sin sufijo de fecha ni timestamp:

```
# output/<job>/ (segun naming_mode configurado)
output/books_to_scrape/books_20260325.csv

# latest/<job>/ (siempre igual, ruta fija)
latest/books_to_scrape/books.csv
```

Esto garantiza que la ruta `latest/<job>/<filename>.<ext>` sea invariante entre ejecuciones y conocida de antemano por el proceso downstream.

## Configuracion

### Global (`config/global_settings.py`)

Aplica a todos los jobs. Contiene unicamente `LOG_CONFIG`.

```python
LOG_CONFIG = {
    "log_folder": "log",                          # Carpeta de logs (compartida entre todos los jobs)
    "level": os.environ.get("LOG_LEVEL", "INFO")  # Nivel: DEBUG, INFO, WARNING, ERROR
}
```

El nivel de log se puede sobreescribir definiendo `LOG_LEVEL` en `.env` sin tocar el codigo:

```
# .env
LOG_LEVEL=DEBUG
```

Cada ejecucion genera su propio archivo de log: `log/<job>_YYYYMMDD_HHMMSS.log`. El timestamp completo garantiza que multiples ejecuciones del mismo dia no mezclen sus logs.

La configuracion de formatos (encoding, separadores, etc.) ya no vive aqui — cada job la declara en `STORAGE_CONFIG["format_config"]` de su propio `settings.py`.

### Por job (`src/<job>/settings.py`)

Especifica del job. Contiene `DRIVER_CONFIG`, `STORAGE_CONFIG` y `SKIP_PROCESS`.

```python
DRIVER_CONFIG = {
    "headless": False,                                       # Ejecutar sin interfaz grafica
    "undetected": True,                                      # Modo anti-deteccion
    "maximize": True,                                        # Maximizar ventana
    "window_size": None,                                     # Tamano especifico: (1920, 1080)
    "user_agent": os.environ.get("SCRAPER_USER_AGENT") or None,  # Leer de .env o None
    "proxy":      os.environ.get("SCRAPER_PROXY")      or None,  # Leer de .env o None
}
```

`user_agent` y `proxy` se leen desde `.env`. El `or None` garantiza que una variable definida como cadena vacia se trate como ausente:

```
# .env
SCRAPER_PROXY=123.45.67.89:8080
SCRAPER_USER_AGENT=Mozilla/5.0 (Windows NT 10.0; Win64; x64)...
```

```python
STORAGE_CONFIG = {
    # --- Output ---
    "output_folder": "output/viviendas_adonde",
    "filename": "viviendas",
    "naming_mode": "date_suffix",    # overwrite | date_suffix | timestamp_suffix | date_folder
    "output_formats": ["csv", "json"],
    #                   ↑ el primer formato tambien define el formato del raw

    # --- Raw ---
    "raw_folder": "raw/viviendas_adonde",
    "retention": {
        "mode": "keep_last_n",  # keep_all | keep_last_n | keep_days
        "value": 5
    },

    # --- Formatos ---
    "format_config": {
        "csv":  {"encoding": "utf-8", "separator": ";", "index": False},
        "json": {"indent": 2, "force_ascii": False, "orient": "records"},
        # Define una entrada por cada formato en output_formats
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

#### Formato del raw

El raw siempre usa el **primer formato de `output_formats`** y su config correspondiente de `format_config`. No hay campo separado para declararlo — se deriva automaticamente:

```python
"output_formats": ["csv", "json"]   # raw → CSV con format_config["csv"]
"output_formats": ["json", "csv"]   # raw → JSON con format_config["json"]
```

#### Politicas de retencion de raw

| Modo | Comportamiento |
|------|----------------|
| `keep_all` | Conserva todos los archivos raw |
| `keep_last_n` | Conserva los ultimos N archivos, ordenados por timestamp en el nombre |
| `keep_days` | Conserva los archivos cuyo timestamp en el nombre no supere N dias de antiguedad |

### Web (`src/<job>/web_config.yaml`)

```yaml
url: "https://ejemplo.com"

# Selectores — indica el tipo usado (XPath o CSS) en un comentario.
selectors:
  container: '//div[@class="item"]'
  Campo1: './/span[@class="dato1"]'
  Campo2: './/span[@class="dato2"]'

waits:
  reconnect_attempts: 3
  after_load: 5
```

## Zonas de trabajo

El proyecto define dos zonas de trabajo diferenciadas, cada una con sus archivos y responsabilidades.

### Zona data engineer

Archivos marcados con `# ZONA DATA ENGINEER`. El data engineer implementa la extraccion, transformacion y configuracion de cada job.

| Archivo | Zona | Que implementar |
|---------|------|-----------------|
| `src/<job>/web_config.yaml` | Completo | `url`, `selectors`, `waits` |
| `src/<job>/settings.py` | Completo | `DRIVER_CONFIG`, `STORAGE_CONFIG` (incluye raw, retencion y `format_config`), `SKIP_PROCESS` |
| `src/<job>/scraper.py` | Cuerpo de `scrape()` | Navegacion, manejo de CAPTCHA, extraccion de elementos |
| `src/<job>/utils.py` | Cuerpo de `parse_record()` | Extraccion campo a campo (texto, atributo, logica especial) |
| `src/<job>/process.py` | Cuerpo de `process()` + constantes de apoyo | Transformaciones, castings de tipo, columnas derivadas |
| `src/consolidadores/<nombre>.py` | `STORAGE_CONFIG` + cuerpo de `consolidate()` | Desempaquetar DataFrames y logica de combinacion |
| `config/pipelines/<nombre>.yaml` | Completo | Jobs, params, bloque `consolidate` |
| `config/global_settings.py` | Completo (casos excepcionales) | Nivel de log, carpeta de logs |

### Zona gobierno de datos

Archivos marcados con `# ZONA GOBIERNO DE DATOS`. El equipo de gobierno implementa las validaciones que deben cumplirse antes de que cualquier output sea persistido.

| Archivo | Zona | Que implementar |
|---------|------|-----------------|
| `src/<job>/validate.py` | Cuerpo de `validate()` | Reglas de calidad, completitud, rangos, formatos esperados |
| `src/consolidadores/<nombre>.py` `validate()` | Cuerpo de `validate()` | Validaciones especificas del dataset consolidado (opcional) |

Lo que **ninguna** zona toca:
- `src/main.py`
- `src/shared/` (job_runner, storage, driver_config, logger, utils)

## Agregar un nuevo proceso

1. Crear `src/<nombre>/scraper.py` con la logica de extraccion
2. Crear `src/<nombre>/utils.py` con `parse_record()` (importa `safe_get_text`/`safe_get_attr` desde `src.shared.utils`)
3. Crear `src/<nombre>/process.py` con la logica de transformacion
4. Crear `src/<nombre>/validate.py` con la funcion `validate()` — obligatorio; dejar la ZONA GOBIERNO DE DATOS vacia hasta que el equipo de gobierno la rellene
5. Crear `src/<nombre>/settings.py` con `DRIVER_CONFIG`, `STORAGE_CONFIG` (con `raw_folder`, `retention` y `format_config`) y `SKIP_PROCESS`
6. Crear `src/<nombre>/web_config.yaml` con la URL y los selectores

Las carpetas `output/<nombre>/` y `raw/<nombre>/` se crean automaticamente en la primera ejecucion. No es necesario modificar `main.py` ni ningun otro modulo del framework — el dispatcher descubre el job automaticamente por la presencia de `scraper.py`.

Luego ejecutar:

```bash
python -m src.main --job <nombre>
```

No es necesario modificar `main.py`.

## Validaciones (`src/<job>/validate.py`)

Cada job requiere un archivo `validate.py` con la funcion `validate()`. El framework la llama despues de `process()` y antes de guardar cualquier output. Si la validacion falla, el job termina con error, no se escribe ningun archivo de output y `latest/` recibe unicamente el log para trazabilidad.

### Dos niveles de severidad

La zona soporta dos niveles de severidad para que el equipo de gobierno distinga entre problemas que invalidan el dataset y anomalias puntuales que conviene registrar pero no bloquean:

| Mecanismo | Efecto | Cuando usarlo |
|-----------|--------|---------------|
| `errors.append(msg)` | Bloquea el guardado, el job termina con error | El problema hace que el dataset sea inutil o incorrecto (ej: 0 registros, campo clave nulo, tipo de dato incorrecto tras el procesamiento) |
| `logger.warning(msg)` | Solo registra en el log, el job continua | Anomalia puntual aceptable que no invalida el dataset completo (ej: pocos nulos en campo no critico, valores en rango inusual) |

```python
def validate(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []

    # =========================================================================
    # ZONA GOBIERNO DE DATOS
    #
    # Dos niveles de severidad:
    #   errors.append(...)  → bloquea el guardado
    #   logger.warning(...) → solo registra, no bloquea
    # =========================================================================

    # 1. Minimo de registros
    # MIN_REGISTROS = 10
    # if len(df) < MIN_REGISTROS:
    #     errors.append(f"Se esperaban al menos {MIN_REGISTROS} registros, se obtuvieron {len(df)}.")

    # 2. Nulos en campos criticos (clave de negocio) → errors; en campos importantes → warning
    # CAMPOS_CRITICOS = ["Titulo"]
    # for campo in CAMPOS_CRITICOS:
    #     if campo in df.columns:
    #         nulos = df[campo].isna() | (df[campo].astype(str).str.strip() == "")
    #         if int(nulos.sum()) > 0:
    #             errors.append(f"Campo critico '{campo}' tiene {int(nulos.sum())} valor(es) nulo(s).")

    # 3. Tipos de dato: si process() debia convertir a numerico y no lo logro → error
    # if "Precio" in df.columns:
    #     no_numericos = pd.to_numeric(df["Precio"], errors="coerce").isna() & df["Precio"].notna()
    #     if int(no_numericos.sum()) > 0:
    #         errors.append(f"'Precio' tiene {int(no_numericos.sum())} valor(es) no numericos.")

    # 4. Rango de valores: anomalias puntuales → warning; sistematicas → errors
    # if "Precio" in df.columns:
    #     n = int((pd.to_numeric(df["Precio"], errors="coerce") <= 0).sum())
    #     if n > 0:
    #         logger.warning(f"'Precio' tiene {n} valor(es) <= 0.")

    # 5. Deduplicacion: red de seguridad sobre lo que process() ya limpio
    #    Nota: la eliminacion de duplicados va en process.py, no aqui.
    # CLAVE_UNICA = ["Titulo"]
    # n = int(df.duplicated(subset=CLAVE_UNICA, keep=False).sum())
    # if n > 0:
    #     errors.append(f"Se encontraron {n} registro(s) duplicados por clave {CLAVE_UNICA}.")

    # =========================================================================
    # FIN ZONA GOBIERNO DE DATOS
    # =========================================================================

    return errors  # lista vacia = validacion exitosa
```

**Contrato:**
- Recibe el DataFrame procesado por `process()` con los tipos ya asignados
- Retorna `list[str]`: lista vacia = exito; lista con mensajes = fallo y guardado bloqueado
- Es de **solo lectura** — no debe modificar el DataFrame (las correcciones van en `process.py`)
- No recibe `params`; si necesita contexto externo debe leerlo desde constantes o archivos de configuracion propios

### Validacion en consolidadores

La funcion `validate()` en un consolidador es **opcional**. Si esta definida, el framework la ejecuta despues de `consolidate()` y antes de guardar el output consolidado. El contrato es identico al de los jobs.

```python
# src/consolidadores/<nombre>.py
def validate(df: pd.DataFrame) -> list[str]:
    errors: list[str] = []
    # ZONA GOBIERNO DE DATOS
    return errors
```

### Comportamiento ante fallo de validacion

| Escenario | Resultado |
|-----------|-----------|
| Job individual falla validacion | Error logueado, no se guarda output, `latest/<job>/` recibe solo el log |
| Job en pipeline falla validacion | Mismo que fallo normal de job: pipeline continua, consolidacion omitida si hay fallos |
| Consolidador falla validacion | Error logueado, no se guarda el consolidado, `latest/<pipeline>/` recibe solo logs de los jobs |

## Historial de runs (`run_history/`)

Cada vez que un job termina (con exito o con error) el framework registra automaticamente el resultado en `run_history/<job_name>.jsonl`. El formato es **JSON Lines**: una linea por ejecucion, cada linea es un objeto JSON valido.

```jsonl
{"job": "books_to_scrape", "started_at": "2026-03-31T14:30:52", "mode": "scrape", "status": "success", "raw_suffix": "20260331_143052", "error": null, "duration_s": 18.4, "outputs": ["output/books_to_scrape/books_20260331.csv"]}
{"job": "books_to_scrape", "started_at": "2026-03-31T20:00:01", "mode": "scrape", "status": "failed", "raw_suffix": null, "error": "El scraper no retorno datos.", "duration_s": 5.1, "outputs": []}
```

| Campo | Descripcion |
|-------|-------------|
| `job` | Nombre del job |
| `started_at` | Timestamp de inicio (ISO 8601) |
| `mode` | `"scrape"` para ejecucion normal, `"reprocess"` para `--reprocess` |
| `status` | `"success"` o `"failed"` |
| `raw_suffix` | Sufijo del archivo raw generado o reprocesado; `null` si el job fallo antes de generarlo |
| `error` | Mensaje de la excepcion capturada; `null` si fue exitoso |
| `duration_s` | Duracion total del run en segundos |
| `outputs` | Lista de rutas de los archivos de output generados; vacia si fallo |

La carpeta `run_history/` esta en `.gitignore` — es datos de runtime de cada instancia, no codigo.

Si un run fallo y quieres reprocesar el raw correspondiente, usa el `raw_suffix` del registro:

```bash
python -m src.main --job books_to_scrape --reprocess 20260331_143052
```

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

`job_runner.py` se encarga de normalizar el raw y construir el DataFrame antes de llamar a `process()`. El modulo no tiene dependencias de I/O — solo recibe datos y devuelve datos.

### Lineamiento string-first

El raw intermedio se persiste siempre como `str`. El output final preserva los tipos que `process.py` asigne:

- **Al escribir raw** (`save_raw`): se aplica `df.fillna("").astype(str)` — los `NaN` reales se rellenan con `""` antes de convertir a string, preservando el literal `"nan"` como dato valido en campos de texto
- **Normalizacion en memoria**: tras `save_raw`, el raw se normaliza en memoria con `pd.DataFrame(datos).fillna("").astype(str)` — todas las columnas llegan a `process()` como `str` sin un ciclo de lectura a disco adicional; `load_raw` queda exclusivo para el flujo `--reprocess`, donde retorna directamente un `pd.DataFrame` listo para pasar a `process()`
- **Al escribir output** (`save_data`): se preservan los tipos que `process.py` asigno (`float`, `int`, `datetime`, etc.) — en JSON los numeros se guardan como numeros, en XLSX las celdas mantienen su tipo

Esto garantiza que valores como `"001"`, `"N/A"`, `"1.500,00"` o registros danados se preserven exactamente como llegan del scraper. La conversion de tipos es responsabilidad exclusiva de `process.py`.

## API Reference

### `src/shared/job_runner.py`

```python
def load_web_config(job_name: str) -> dict:
    """Carga y valida la configuracion de la web desde src/<job_name>/web_config.yaml.
    Lanza ValueError si faltan las claves requeridas (url, selectors, waits)."""

def run(args, scrape_fn, process_fn, validate_fn, settings, job_name: str, params: dict | None = None, update_latest: bool = True) -> dict[str, Path]:
    """
    Punto de entrada generico para cualquier job. Llamado directamente desde main.py.
    params: dict nativo con los parametros definidos en el pipeline YAML (vacio si no se definio ninguno).
    validate_fn: funcion validate() del job; se ejecuta despues de process() y antes de save_data().
    update_latest: si True (default) gestiona latest/<job>/ al inicio y al final de la ejecucion.
                   El orquestador de pipelines consolidados lo pasa como False para gestionar
                   su propio latest/<pipeline_name>/ centralizado.
    Retorna mapa de formato -> ruta del archivo guardado (ej: {"csv": Path(...), "json": Path(...)}).

    Flujo completo:    scrape → save_raw → normalize_in_memory → process(df) → validate(df) → cleanup_raw → save_data → copy_to_latest
    Sin proceso:       scrape → save_raw → normalize_in_memory → validate(df) → cleanup_raw → save_data → copy_to_latest
    Flujo reprocess:   load_raw → process(df) → validate(df) → save_data → copy_to_latest
    En todos los flujos se loguea el tiempo de cada etapa: [scrape] Xs | [process] Xs | [validate] Xs | OK | [save] Xs | N formato(s)
    """
```

### `src/shared/storage.py`

```python
def get_format_config(storage_config: dict, format: str) -> dict:
    """Retorna la config del formato desde storage_config["format_config"].
    Si no esta definida, usa los defaults internos del framework como red de seguridad."""

def save_data(datos, format, storage_config, now=None) -> Path:
    """Guarda los datos en el formato y ubicacion especificados preservando los tipos de cada campo.
    La config del formato se extrae de storage_config["format_config"].
    now: datetime opcional; si se omite se usa datetime.now(). Pasar el mismo valor que a save_raw()
    garantiza timestamps coherentes entre el raw y el output de una misma ejecucion.
    Retorna la ruta del archivo guardado."""

def save_raw(datos: pd.DataFrame, storage_config, now=None) -> str:
    """Guarda datos en bruto usando output_formats[0] como formato. Retorna el sufijo timestamp.
    datos: DataFrame ya construido (string-first). El caller es responsable de construirlo.
    now: datetime opcional; si se omite se usa datetime.now(). Pasar el mismo valor que a save_data()
    garantiza coherencia de timestamps entre raw y output."""

def load_output(filepath: Path, format: str, storage_config: dict) -> pd.DataFrame:
    """Lee un archivo de output y lo retorna como DataFrame usando format_config del job.
    Usada por el runner para preparar los DataFrames antes de pasarlos al consolidador."""

def load_raw(suffix, storage_config) -> pd.DataFrame:
    """Lee un raw existente y lo retorna como DataFrame sin transformar. Lee todo como str.
    El formato se deriva de storage_config["output_formats"][0]."""

def cleanup_raw(storage_config) -> None:
    """Limpia archivos raw segun la politica de retencion configurada."""

def build_filepath(storage_config, format, now=None) -> Path:
    """Construye la ruta del archivo segun el modo de nombrado configurado.
    now: datetime opcional; si se omite se usa datetime.now()."""

def clear_latest(folder: str) -> None:
    """Borra y recrea latest/<folder>/ antes de cada ejecucion para garantizar un estado limpio."""

def copy_to_latest(folder: str, output_paths: dict[str, Path], log_path: Path | None, base_filename: str | None = None) -> None:
    """Copia los outputs a latest/<folder>/ renombrandolos a <base_filename>.<ext> (ruta fija).
    Copia el log como run.log. Si output_paths esta vacio (fallo), solo copia el log."""

def merge_logs_to_latest(folder: str, log_paths: list[Path]) -> None:
    """Concatena multiples logs en latest/<folder>/run.log con separadores por seccion.
    Usado por pipelines con consolidacion para unificar los logs de todos los jobs."""
```

### `src/shared/logger.py`

```python
def setup_logger(job_name: str, now: datetime, log_folder: str = "log", level: str = "INFO") -> None:
    """
    Configura el logger "src" para el job indicado. Thread-safe.
    En modo secuencial actualiza _local.log_path al nuevo archivo.
    En modo paralelo cada hilo mantiene su propio _local.log_path y escribe
    en su propio archivo sin interferir con otros hilos.
    """

def get_current_log_path() -> Path | None:
    """Retorna el Path del log activo en el hilo actual. None si no hay log configurado."""

def flush_log() -> None:
    """
    Flushea y cierra el FileHandler del hilo actual.
    Libera el descriptor de archivo — evita leaks en pipelines con muchos jobs.
    Debe llamarse al finalizar cada job antes de copiar el log a latest/.
    get_current_log_path() sigue retornando el path correcto tras flush_log().
    """
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
def scrape(driver, web_config, params: dict) -> list[dict]:
    """
    Extrae datos desde la URL usando los selectores del archivo de configuracion.
    params: dict nativo con los parametros definidos en el pipeline YAML.
    Los tipos se preservan directamente (int, bool, float, str) — no se requiere conversion manual.
    """
```

### `src/<job>/process.py`

```python
def process(df: pd.DataFrame) -> list[dict]:
    """Recibe un DataFrame con columnas en str y aplica transformaciones y castings de tipo."""
```

### `src/<job>/validate.py`

```python
def validate(df: pd.DataFrame) -> list[str]:
    """
    Valida el DataFrame procesado antes de guardarlo.
    Recibe el DataFrame con los tipos asignados por process(). Es de solo lectura.
    Retorna lista de mensajes de error; lista vacia significa validacion exitosa.
    Si retorna errores, el job falla: no se guarda output ni se actualiza latest/ con datos.
    """
```

### `src/<job>/utils.py`

```python
def parse_record(item, selectors, index) -> dict:
    """Construye el diccionario de un registro a partir de un elemento contenedor.
    Implementa la logica especifica del job para cada campo (texto, atributo, etc.).
    Importa safe_get_text y safe_get_attr desde src.shared.utils."""
```

## Tests

### `tests/test_global.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestLogConfig` | `test_global_settings_has_log_config` | Verifica que LOG_CONFIG existe |
| `TestLogConfig` | `test_log_config_has_required_keys` | Valida claves requeridas |
| `TestLogConfig` | `test_log_config_level_is_valid` | Valida nivel de logging |

### `tests/test_pipelines.py`

Valida automaticamente todos los `.yaml` presentes en `config/pipelines/` — no requiere actualizacion al agregar nuevos pipelines.

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestPipelineYAML` | `test_at_least_one_pipeline_exists` | Existe al menos un pipeline en `config/pipelines/` |
| `TestPipelineYAML` | `test_pipelines_have_jobs_list` | `jobs` existe, es lista y no esta vacia |
| `TestPipelineYAML` | `test_pipeline_jobs_have_name` | Cada job tiene `name` como string no vacio |
| `TestPipelineYAML` | `test_pipeline_job_names_exist_in_src` | Los nombres de job corresponden a jobs reales en `src/` |
| `TestPipelineYAML` | `test_pipeline_params_are_dicts_if_present` | `params` es dict nativo YAML, no string |
| `TestPipelineYAML` | `test_pipeline_enabled_is_bool_if_present` | `enabled` es `true` o `false` |
| `TestPipelineYAML` | `test_pipeline_metadata_types_if_present` | `name` y `description` del pipeline son strings |
| `TestPipelineYAML` | `test_consolidate_structure_if_present` | Valida estructura del bloque `consolidate` cuando esta presente |
| `TestPipelineYAML` | `test_consolidate_module_exists_if_enabled` | El modulo consolidador existe en `src/consolidadores/` cuando `enabled: true` |
| `TestPipelineYAML` | `test_consolidate_format_in_all_jobs_if_enabled` | Todos los jobs activos incluyen el `format` de consolidacion en su `output_formats` |
| `TestPipelineYAML` | `test_consolidate_format_config_compatible` | Todos los jobs comparten la misma `format_config` para el formato de consolidacion |

### `tests/viviendas_adonde/test_viviendas_adonde.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestWebConfig` | `test_web_config_file_exists` | Verifica existencia del YAML |
| `TestWebConfig` | `test_web_config_has_required_keys` | Valida claves requeridas |
| `TestWebConfig` | `test_url_format_is_valid` | Valida formato URL |
| `TestWebConfig` | `test_selectors_format` | Valida que cada selector es una cadena no vacia (XPath o CSS) |
| `TestWebConfig` | `test_waits_are_positive_numbers` | Valida waits numericos |
| `TestStorageConfig` | `test_settings_has_storage_config` | Verifica STORAGE_CONFIG existe |
| `TestStorageConfig` | `test_storage_config_has_required_keys` | Valida las 7 claves requeridas (incluye `raw_folder`, `retention`, `format_config`) |
| `TestStorageConfig` | `test_storage_config_naming_mode_is_valid` | Valida naming_mode |
| `TestStorageConfig` | `test_storage_config_output_folder_is_valid_path` | Verifica que output_folder es una cadena no vacia |
| `TestStorageConfig` | `test_storage_config_raw_folder_is_valid_path` | Verifica que raw_folder es una cadena no vacia |
| `TestStorageConfig` | `test_storage_config_output_formats_are_valid` | Valida formatos de salida |
| `TestStorageConfig` | `test_storage_config_retention_mode_is_valid` | Valida modo de retencion |
| `TestStorageConfig` | `test_storage_config_format_config_covers_output_formats` | Verifica que format_config define una entrada por cada formato en output_formats |
| `TestDriverConfig` | `test_settings_file_has_driver_config` | Verifica DRIVER_CONFIG existe |
| `TestDriverConfig` | `test_driver_instance_created_with_settings_file` | Test de instancia del driver |

### `tests/books_to_scrape/test_books_to_scrape.py`

| Clase | Test | Descripcion |
|-------|------|-------------|
| `TestWebConfig` | `test_web_config_file_exists` | Verifica existencia del YAML |
| `TestWebConfig` | `test_web_config_has_required_keys` | Valida claves requeridas |
| `TestWebConfig` | `test_url_format_is_valid` | Valida formato URL |
| `TestWebConfig` | `test_selectors_format` | Valida que cada selector es una cadena no vacia (XPath o CSS) |
| `TestWebConfig` | `test_selectors_has_expected_fields` | Verifica campos Titulo, Precio y Rating |
| `TestWebConfig` | `test_waits_are_positive_numbers` | Valida waits numericos |
| `TestStorageConfig` | `test_settings_has_storage_config` | Verifica STORAGE_CONFIG existe |
| `TestStorageConfig` | `test_storage_config_has_required_keys` | Valida las 7 claves requeridas (incluye `raw_folder`, `retention`, `format_config`) |
| `TestStorageConfig` | `test_storage_config_naming_mode_is_valid` | Valida naming_mode |
| `TestStorageConfig` | `test_storage_config_output_folder_is_valid_path` | Verifica que output_folder es una cadena no vacia |
| `TestStorageConfig` | `test_storage_config_raw_folder_is_valid_path` | Verifica que raw_folder es una cadena no vacia |
| `TestStorageConfig` | `test_storage_config_output_formats_are_valid` | Valida formatos de salida |
| `TestStorageConfig` | `test_storage_config_retention_mode_is_valid` | Valida modo de retencion |
| `TestStorageConfig` | `test_storage_config_format_config_covers_output_formats` | Verifica que format_config define una entrada por cada formato en output_formats |
| `TestDriverConfig` | `test_settings_file_has_driver_config` | Verifica DRIVER_CONFIG existe |
| `TestDriverConfig` | `test_driver_instance_created_with_settings_file` | Test de instancia del driver |

## Dependencias

Las versiones estan pinadas con el operador `~=` (compatible release): permite actualizaciones de patch pero bloquea saltos de version mayor que puedan romper la API.

| Paquete | Uso |
|---|---|
| `seleniumbase` | Automatizacion de navegador con soporte anti-deteccion |
| `pandas` | Manipulacion y exportacion de datos |
| `pyyaml` | Lectura de archivos de configuracion YAML |
| `pytest` | Framework de tests |
| `openpyxl` | Exportacion a Excel (.xlsx) |
| `python-dotenv` | Carga de variables de entorno desde `.env` |

## Licencia

Este proyecto es open source y esta disponible bajo la [Licencia MIT](LICENSE).

## Aviso Legal

Esta plantilla esta destinada exclusivamente para fines educativos y de aprendizaje. Antes de realizar scraping en cualquier sitio web, asegurate de:

- Revisar y respetar los terminos de servicio del sitio
- Consultar el archivo `robots.txt`
- No sobrecargar los servidores con peticiones excesivas
- Respetar la privacidad y los datos personales

El uso responsable del web scraping es responsabilidad del usuario.
