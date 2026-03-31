# Changelog

## [0.45.0] - 2026-03-30

### Added
- `src/shared/storage.py` `get_format_config(storage_config, format)`: nueva funcion publica que extrae la config de escritura/lectura de un formato desde `storage_config["format_config"]`; si la clave no esta definida actua como red de seguridad y retorna los defaults internos del framework (`_FORMAT_DEFAULTS`); usada internamente por todas las funciones de I/O y externamente por `main.py` en la validacion de consolidacion
- `src/shared/storage.py` `_FORMAT_DEFAULTS`: constante interna con los valores por defecto para todos los formatos soportados; actua unicamente como fallback cuando `format_config` no esta definido en `STORAGE_CONFIG`
- `tests/test_pipelines.py` `test_consolidate_format_config_compatible`: nuevo test que verifica que todos los jobs activos de un pipeline consolidado comparten la misma `format_config` para el formato de consolidacion; usa `get_format_config` para comparar las configs efectivas
- `tests/<job>/test_<job>.py` `TestStorageConfig.test_storage_config_raw_folder_is_valid_path`: nuevo test que verifica que `raw_folder` es una cadena no vacia en ambos jobs
- `tests/<job>/test_<job>.py` `TestStorageConfig.test_storage_config_retention_mode_is_valid`: nuevo test que verifica que el modo de retencion es uno de los valores soportados
- `tests/<job>/test_<job>.py` `TestStorageConfig.test_storage_config_format_config_covers_output_formats`: nuevo test que verifica que `format_config` define una entrada (dict no vacio) por cada formato declarado en `output_formats`

### Changed
- `src/<job>/settings.py` (x2): `RAW_CONFIG` eliminado como variable independiente — sus campos (`raw_folder`, `retention`) se absorben en `STORAGE_CONFIG`; se agrega la clave `format_config` en `STORAGE_CONFIG` con las opciones de escritura/lectura para cada formato usado por el job; el formato del raw ya no se declara explicitamente — se deriva del primer elemento de `output_formats`
- `src/consolidadores/ejemplo.py`: `STORAGE_CONFIG` incorpora la nueva clave `format_config` con la config del formato de consolidacion; el comentario de restriccion actualizado para reflejar la nueva validacion de compatibilidad de configs
- `config/global_settings.py`: eliminado el bloque `DATA_CONFIG` — ya no es necesario porque cada job gestiona su propia config de formatos; el comentario del archivo actualizado para reflejar que la config de formatos vive en `STORAGE_CONFIG["format_config"]` de cada job
- `src/shared/storage.py` `save_data()`: firma simplificada de `(datos, format, data_config, storage_config, now)` a `(datos, format, storage_config, now)` — `data_config` eliminado; la config del formato se extrae internamente via `get_format_config`
- `src/shared/storage.py` `save_raw()`: firma simplificada de `(datos, raw_config, data_config, now)` a `(datos, storage_config, now)` — `raw_config` y `data_config` eliminados; el formato del raw se deriva de `storage_config["output_formats"][0]`; la config del formato se extrae via `get_format_config`
- `src/shared/storage.py` `load_output()`: firma simplificada de `(filepath, format, data_config)` a `(filepath, format, storage_config)` — usa `get_format_config` para extraer la config del job
- `src/shared/storage.py` `load_raw()`: firma simplificada de `(suffix, raw_config, data_config)` a `(suffix, storage_config)` — el formato y su config se derivan del `storage_config` del job
- `src/shared/storage.py` `cleanup_raw()`: firma simplificada de `(raw_config)` a `(storage_config)` — extrae `raw_folder`, formato y retencion directamente del `storage_config`
- `src/shared/job_runner.py`: eliminada la referencia a `global_settings.DATA_CONFIG` en las llamadas a `save_raw`, `load_raw` y `save_data`; todas las funciones de storage reciben ahora solo `settings.STORAGE_CONFIG`; `cleanup_raw` actualizado a `cleanup_raw(settings.STORAGE_CONFIG)`
- `src/main.py`: eliminada la importacion de `global_settings` (ya no se usa en este modulo); importado `get_format_config` desde `storage`; `_validate_consolidation` ampliada con un segundo chequeo que compara la `format_config` efectiva de todos los jobs para el formato de consolidacion y falla con mensaje detallado si difieren; `_run_consolidation` actualizado para cargar dinamicamente el `settings` de cada job y usar `load_output(filepath, fmt, job_settings.STORAGE_CONFIG)` en lugar del `DATA_CONFIG` global
- `tests/test_global.py`: eliminada la clase `TestDataConfig` (sus dos tests validaban `DATA_CONFIG` en `global_settings`, que ya no existe)
- `tests/<job>/test_<job>.py` (x2): eliminada la clase `TestRawConfig` (sus cuatro tests validaban `RAW_CONFIG`, que ya no existe); `TestStorageConfig.test_storage_config_has_required_keys` actualizado para exigir las 7 claves del nuevo `STORAGE_CONFIG` unificado

## [0.44.0] - 2026-03-25

### Added
- `src/<job>/validate.py` (x2, nuevos): archivo obligatorio por job con la funcion `validate(df) -> list[str]`; contiene la ZONA GOBIERNO DE DATOS lista para que el equipo de gobierno implemente sus validaciones; lista vacia = validacion exitosa, lista con mensajes = fallo con errores descriptivos
- `src/shared/job_runner.py` `_run_validate(validate_fn, processed)`: nueva funcion interna que ejecuta `validate()` sobre el DataFrame procesado antes de guardar; lanza `ValueError` con todos los mensajes de error si la validacion falla
- `src/consolidadores/ejemplo.py` `validate(df)`: funcion opcional de validacion para el consolidador con ZONA GOBIERNO DE DATOS; el framework la detecta con `hasattr` y la ejecuta si existe, antes de guardar el output consolidado

### Changed
- `src/shared/job_runner.py` `run()`: nuevo parametro `validate_fn`; `_run_validate()` se ejecuta despues de `process()` y antes de `save_data()` — si falla, no se guarda ningun output pero `latest/` recibe el log para trazabilidad
- `src/main.py` `_load_job_parts()`: carga `src/<job>/validate.py` de forma obligatoria; si el archivo no existe lanza `SystemExit(1)` con mensaje descriptivo indicando como crearlo
- `src/main.py` `_run_consolidation()`: ejecuta `consolidator.validate()` si esta definida, entre `consolidate()` y `save_data()`; un fallo de validacion lanza `ValueError` que es capturado por `_run_series()` para actualizar `latest/` con solo el log
- `src/main.py` `_run_series()`: el bloque de consolidacion se envuelve en try/except/finally para garantizar que `latest/` se actualice con el log incluso si la validacion del consolidador falla
- `src/consolidadores/ejemplo.py`: marcador `# FIN ZONA DATA ENGINEER (2/2)` movido a antes del `return` (era codigo inalcanzable tras el return)

## [0.43.0] - 2026-03-25

### Added
- `latest/` — nueva carpeta que actua como espejo de la ultima ejecucion de cada job o pipeline; proporciona rutas fijas y estables para procesos downstream sin depender del `naming_mode` configurado en cada job
- `src/shared/storage.py` `clear_latest(folder)`: borra y recrea `latest/<folder>/` al inicio de cada ejecucion garantizando un estado limpio
- `src/shared/storage.py` `copy_to_latest(folder, output_paths, log_path, base_filename)`: copia los outputs con nombre fijo (`<filename>.<ext>`) y el log de la ejecucion como `run.log` a `latest/<folder>/`; si el job fallo y no hay outputs, solo se copia el log para mantener trazabilidad
- `src/shared/storage.py` `merge_logs_to_latest(folder, log_paths)`: concatena los logs de multiples jobs en un unico `latest/<folder>/run.log` con separadores por seccion; usado exclusivamente por pipelines con consolidacion
- `src/shared/logger.py` `current_log_path`: variable de modulo que registra la ruta del archivo de log activo tras cada llamada a `setup_logger()`; permite al framework copiar el log correcto a `latest/` sin acoplamiento entre modulos
- `src/shared/logger.py` `flush_log()`: fuerza el flush de todos los handlers del logger `"src"` antes de copiar el archivo de log a `latest/`

### Changed
- `src/shared/job_runner.py` `run()`: nuevo parametro `update_latest=True` — cuando es `True` (default) limpia y actualiza `latest/<job>/` al inicio y al final de cada ejecucion (tanto en exito como en fallo); cuando es `False` delega la gestion de `latest/` al orquestador del pipeline consolidado
- `src/main.py` `_run_series()`: nuevo parametro `pipeline_name` — en pipelines con consolidacion activa gestiona un unico `latest/<pipeline_name>/` con el output consolidado y los logs de todos los jobs concatenados; los jobs individuales no escriben en `latest/` en este modo (`update_latest=False`)
- `src/main.py` `_run_consolidation()`: pasa de retornar `None` a retornar `dict[str, Path]` con el mapa formato → ruta del archivo consolidado; permite al orquestador copiar el output a `latest/` sin reimportar el modulo consolidador
- `src/main.py` `_load_pipeline()`: pasa de retornar `tuple[list, dict | None]` a `tuple[list, dict | None, str | None]` incluyendo el nombre del pipeline; usado para nombrar la carpeta en `latest/` en pipelines consolidados
- `src/shared/logger.py` `setup_logger()`: actualiza `current_log_path` en cada llamada para que el framework siempre tenga acceso a la ruta del log activo

## [0.42.0] - 2026-03-24

### Added
- `README.md`: nueva seccion **"Zonas del data engineer"** con tabla de referencia rapida que mapea cada archivo a su zona editable y describe que implementar en cada una

### Changed
- `src/<job>/scraper.py` (x2): marcador `# ZONA DATA ENGINEER` al inicio del cuerpo de `scrape()` — delimita toda la logica de navegacion y extraccion
- `src/<job>/utils.py` (x2): marcador `# ZONA DATA ENGINEER` al inicio del cuerpo de `parse_record()` — delimita la extraccion campo a campo
- `src/<job>/process.py` (x2): marcadores de apertura y cierre en el cuerpo de `process()` — el cierre se coloca justo antes del `return df.to_dict(orient="records")` para dejar claro que ese contrato pertenece al framework; en `books_to_scrape/process.py` el marcador de apertura se situa a nivel de modulo para incluir tambien las constantes de apoyo (ej: `_RATING_MAP`)
- `src/<job>/settings.py` (x2): marcador `# ZONA DATA ENGINEER` tras el docstring del modulo — indica que todo el archivo es territorio del data engineer
- `src/<job>/web_config.yaml` (x2): marcador `# ZONA DATA ENGINEER` al inicio del archivo
- `src/consolidadores/ejemplo.py`: dos marcadores numerados — `(1/2)` alrededor de `STORAGE_CONFIG` y `(2/2)` al inicio del cuerpo de `consolidate()`
- `config/global_settings.py`: marcador con nota de "casos excepcionales" (encoding, separadores, nivel de log)
- `config/pipelines/diario.yaml`, `config/pipelines/diario_consolidado.yaml`: marcador `# ZONA DATA ENGINEER` antes del contenido editable de cada pipeline

## [0.41.0] - 2026-03-24

### Fixed
- `src/main.py` `_run_consolidation()`: variable shadowing — la variable `fmt` del loop `for fmt in output_formats` sobreescribia la variable exterior `fmt = consolidate_config["format"]`; renombradas a `consolidation_fmt` y `output_fmt` respectivamente
- `src/shared/storage.py` `load_raw()`: eliminada doble conversion innecesaria `DataFrame → list[dict] → DataFrame` — la funcion ahora retorna `pd.DataFrame` directamente en lugar de `list[dict]`; `_run_reprocess` actualizado para consumirlo sin envoltura adicional
- `src/shared/storage.py` `save_raw()`: eliminado doble `astype(str)` — el DataFrame ya llega normalizado (string-first) desde `job_runner`; `_write_df` se invoca con `stringify=False`
- `src/main.py` logger del orquestador: los mensajes de pipeline (`[1/2] Iniciando job`, `Serie finalizada`, etc.) se escribian en el archivo de log del ultimo job ejecutado porque `setup_logger()` eliminaba todos los handlers de `"src"`, incluyendo el del orquestador; el logger de `main.py` pasa a usar el namespace `"orchestrator"` (separado de `"src"`) y `_setup_console_handler` lo configura sobre ese mismo logger — `setup_logger()` nunca lo toca
- `src/shared/job_runner.py` `run()`: `cleanup_raw()` no se ejecutaba si el job fallaba durante `process()`, permitiendo que los archivos raw se acumularan sin limite; movido a bloque `finally` para que la politica de retencion se aplique siempre, tanto en exito como en fallo

### Added
- `src/shared/job_runner.py` `_validate_web_config()`: nueva funcion privada que valida las claves requeridas de `web_config.yaml` antes de ejecutar el scraper — verifica que existan `url`, `selectors` (dict no vacio) y `waits` (dict); lanza `ValueError` con mensaje descriptivo si falta alguna; el selector `container` dentro de `selectors` no se valida intencionalmente (es decision del job usarlo o no); llamada desde `load_web_config()`

### Changed
- `src/shared/storage.py` `_write_df()`: el parametro `index` de CSV cambia de `False` hardcodeado a `config.get("index", False)` — consistente con el comportamiento de XLSX que ya lo leia de la config
- `config/global_settings.py` `DATA_CONFIG["xml"]`: agregada clave `"encoding": "utf-8"` — `_write_df` ahora la pasa a `df.to_xml()`, igualando el encoding de escritura al de lectura (que ya usaba `config.get("encoding", "utf-8")` en `_read_df`)

## [0.40.0] - 2026-03-24

### Added
- `src/consolidadores/__init__.py`: nuevo paquete Python para alojar los modulos consolidadores
- `src/consolidadores/ejemplo.py`: consolidador de ejemplo con `STORAGE_CONFIG` y funcion `consolidate(job_dataframes, params)` — el data engineer desempaqueta los DataFrames por nombre y escribe solo logica de negocio; el I/O lo maneja el framework
- `config/pipelines/diario_consolidado.yaml`: pipeline de ejemplo con consolidacion activada — ejecuta `books_to_scrape` y `viviendas_adonde` y consolida los resultados en `output/consolidados/`
- `src/main.py` `_validate_consolidation()`: nueva funcion que valida antes de correr cualquier job que `consolidate.format` este definido, sea un formato soportado, `consolidate.module` exista, y que todos los jobs del pipeline incluyan ese formato en su `output_formats`; falla rapido con mensaje claro si alguna condicion no se cumple
- `src/main.py` `_run_consolidation()`: nueva funcion que carga dinamicamente `src/consolidadores/<module>.py`, lee los outputs de cada job como DataFrames via `load_output()`, llama `consolidate(job_dataframes, params)` y persiste el resultado usando `save_data()` con el `STORAGE_CONFIG` del propio consolidador
- `src/shared/storage.py` `load_output()`: nueva funcion publica que lee un archivo de output y lo retorna como `pd.DataFrame` usando la config correcta de `DATA_CONFIG`; usada por el runner para preparar los DataFrames antes de consolidar
- `tests/test_pipelines.py` `test_consolidate_structure_if_present`: valida estructura del bloque `consolidate` cuando esta presente (`enabled` bool, `module` string no vacio, `format` en formatos soportados, `params` dict si aparece)
- `tests/test_pipelines.py` `test_consolidate_module_exists_if_enabled`: verifica que el modulo consolidador exista en `src/consolidadores/` cuando `enabled: true`
- `tests/test_pipelines.py` `test_consolidate_format_in_all_jobs_if_enabled`: verifica que todos los jobs activos del pipeline incluyan el `format` de consolidacion en su `output_formats`

### Changed
- `src/shared/storage.py` `save_data()`: firma actualizada de `-> None` a `-> Path` — retorna la ruta del archivo guardado; permite al runner acumular los paths generados en cada job para pasarlos al consolidador
- `src/shared/job_runner.py` `_save_output()`: actualizado para capturar los paths retornados por `save_data()` y retornarlos como `dict[str, Path]` (`{"csv": Path(...), "json": Path(...)}`)
- `src/shared/job_runner.py` `run()`: firma actualizada de `-> None` a `-> dict[str, Path]` — retorna el mapa de formato -> ruta generada en esa ejecucion
- `src/main.py` `_load_pipeline()`: firma actualizada de `-> list[dict]` a `-> tuple[list[dict], dict | None]` — retorna ademas el bloque `consolidate` del YAML (o `None` si no existe)
- `src/main.py` `_run_series()`: acepta `consolidate_config` opcional; acumula `job_outputs` durante la serie; ejecuta la consolidacion al final si todos los jobs fueron exitosos
- `config/pipelines/diario.yaml`: ampliado el bloque de comentarios con documentacion del bloque `consolidate` y ejemplo comentado listo para descomentar

### Behavior
```
# Pipeline sin consolidacion (comportamiento anterior, sin cambios)
python -m src.main --pipeline config/pipelines/diario.yaml

# Pipeline con consolidacion
python -m src.main --pipeline config/pipelines/diario_consolidado.yaml
# → jobs corren en serie
# → si todos exitosos: consolida outputs en output/consolidados/<nombre>_<fecha>.<formato>
# → si algun job falla: consolidacion omitida, se registra advertencia
```

### Design decisions
- El framework carga los archivos de cada job como DataFrames antes de llamar a `consolidate()` — el data engineer recibe datos listos, nunca paths ni I/O
- La consolidacion solo corre si **todos** los jobs del pipeline fueron exitosos — datos parciales no consolidan
- La validacion de formato compartido ocurre **antes** de lanzar cualquier job — fallo rapido, no a mitad del pipeline
- El consolidador es autocontenido: define su propio `STORAGE_CONFIG` (carpeta, nombre, naming_mode, formatos de salida)
- Output del consolidado en `output/consolidados/` con naming por fecha por defecto

## [0.39.0] - 2026-03-24

### Changed
- `src/books_to_scrape/web_config.yaml`, `src/viviendas_adonde/web_config.yaml`: renombrada clave `xpath_selectors` → `selectors` — el nombre anterior asumia XPath; la clave ahora es neutral para soportar XPath o CSS segun el job; el tipo usado se documenta en un comentario dentro del propio YAML
- `src/books_to_scrape/scraper.py`, `src/viviendas_adonde/scraper.py`: actualizada clave `web_config["xpath_selectors"]` → `web_config["selectors"]` y docstring correspondiente
- `tests/books_to_scrape/test_books_to_scrape.py` `TestWebConfig`: renombrado `test_xpath_selectors_format` → `test_selectors_format`; la validacion ya no fuerza patron XPath — si el selector empieza con `/` o `./` se reporta como XPath valido, de lo contrario se acepta como CSS siempre que sea una cadena no vacia
- `tests/viviendas_adonde/test_viviendas_adonde.py` `TestWebConfig`: idem anterior
- `tests/books_to_scrape/test_books_to_scrape.py` `TestWebConfig`: renombrado `test_xpath_selectors_has_expected_fields` → `test_selectors_has_expected_fields`; actualizada clave a `selectors`
- `README.md`: actualizados arbol de estructura, ejemplo de `web_config.yaml` y tablas de tests para reflejar el renombre

## [0.38.0] - 2026-03-24

### Changed
- `tests/books_to_scrape/test_books_to_scrape.py` `TestWebConfig`: eliminado `test_xpath_selectors_has_container` — el selector `container` es opcional; cada job decide si lo usa
- `tests/viviendas_adonde/test_viviendas_adonde.py` `TestWebConfig`: eliminado `assert "container" in selectors` de `test_xpath_selectors_format` por la misma razon

### Removed
- `tests/books_to_scrape/test_books_to_scrape.py`: eliminadas clases `TestProcess` y `TestUtils` junto a sus imports (`pd`, `MagicMock`, `process`, `safe_get_text`, `safe_get_attr`, `parse_record`) — estos tests son especificos del job de ejemplo y no forman parte del contrato del framework

### Added
- `tests/test_pipelines.py`: nuevo archivo con `TestPipelineYAML` — valida automaticamente todos los `.yaml` en `config/pipelines/` sin necesidad de actualizarlo al agregar nuevos pipelines:
  - `test_at_least_one_pipeline_exists`: existe al menos un pipeline en `config/pipelines/`
  - `test_pipelines_have_jobs_list`: `jobs` existe, es lista y no esta vacia
  - `test_pipeline_jobs_have_name`: cada job tiene `name` como string no vacio
  - `test_pipeline_job_names_exist_in_src`: los nombres de job corresponden a jobs reales en `src/`
  - `test_pipeline_params_are_dicts_if_present`: `params` es dict nativo YAML, no string
  - `test_pipeline_enabled_is_bool_if_present`: `enabled` es `true` o `false`
  - `test_pipeline_metadata_types_if_present`: `name` y `description` del pipeline son strings

## [0.37.0] - 2026-03-24

### Removed
- `config/pipelines/*.yaml`: eliminado el campo `reprocess` por job — el reprocesamiento es una operacion manual puntual (re-correr `process.py` tras corregir logica) y no debe automatizarse en un pipeline; queda exclusivo del CLI con `--job --reprocess <sufijo>`
- `src/main.py` `_make_args()`: eliminado parametro `reprocess` — siempre es `None` en el contexto de pipeline; el valor real de `--reprocess` solo existe en el `args` del flujo `--job`
- `src/main.py` `_run_series()`: eliminada extraccion de `reprocess` del entry del pipeline
- `src/main.py` `_load_pipeline()`: eliminada lectura del campo `reprocess` por job y su inclusion en las entradas

### CLI
```bash
# --reprocess exclusivo de --job (operacion manual)
python -m src.main --job books_to_scrape --reprocess 20260323_142546

# --pipeline nunca reprocesa, siempre scrapea
python -m src.main --pipeline config/pipelines/diario.yaml
```

## [0.36.0] - 2026-03-24

### Removed
- `src/main.py`: eliminados `--jobs` y `--all` — ambos modos corrían jobs en serie sin soporte de params, `enabled` ni `reprocess` por job; son redundantes con `--pipeline` (que cubre todos esos casos) y creaban una API de segunda clase; el CLI queda con dos modos ortogonales: `--job` para un job individual y `--pipeline` para ejecución en serie con control total
- `src/main.py` `_make_args()`: eliminados `jobs` y `all` del `Namespace` — ya no se usan en ningún flujo

### Changed
- `src/main.py`: mensaje de error del parser actualizado de `--job, --jobs, --all o --pipeline` a `--job o --pipeline`

### CLI
```
# Antes (eliminado)
python -m src.main --jobs books_to_scrape,viviendas_adonde
python -m src.main --all

# Ahora: usar --pipeline con un YAML (incluso sin params es más explícito)
python -m src.main --pipeline config/pipelines/diario.yaml
```

## [0.35.0] - 2026-03-23

### Removed
- `src/main.py`: eliminados `--params` y `--no-params` del CLI — el formato `"clave=valor&clave2=valor2"` no soporta tipos nativos (todos los valores llegaban como `str`), era propenso a errores y duplicaba un mecanismo ya disponible en el pipeline YAML; los params se definen ahora exclusivamente en el YAML del pipeline
- `src/shared/job_runner.py`: eliminadas `_parse_params()`, `_save_last_params()` y `_load_last_params()` — el sistema de persistencia en `.state/<job>_params.json` pierde su razon de existir al centralizar los params en el YAML; el directorio `.state/` ya no se genera en runtime
- `src/shared/job_runner.py`: eliminado `import json` — ya no se usa tras la eliminacion del sistema `.state/`

### Changed
- `config/pipelines/diario.yaml`: params migrados de string URL-encoded (`"clave=valor&clave2=valor2"`) a dict nativo YAML — los tipos se preservan directamente (`pagina: 1` llega como `int`, `solo_nuevos: true` como `bool`, sin conversion manual en el scraper)
- `src/shared/job_runner.py` `run()`: firma actualizada de `run(args, ..., job_name)` a `run(args, ..., job_name, params: dict | None = None)` — los params se reciben como dict nativo en lugar de derivarse de `args`
- `src/main.py` `_make_args()`: eliminados `params` y `no_params` del `Namespace` — ya no forman parte del flujo de ejecucion
- `src/main.py` `_run_series()`: extrae `params` (dict) y `reprocess` del entry y los pasa directamente a `job_runner.run()`

### Added
- `config/pipelines/diario.yaml`: metadatos a nivel de pipeline — campo `name` (mostrado en log al ejecutar) y `description` (opcional)
- `config/pipelines/diario.yaml`: campo `enabled` por job — `enabled: false` omite el job sin necesidad de borrarlo del YAML; `true` por defecto
- `config/pipelines/diario.yaml`: campo `reprocess` por job — permite forzar reprocesamiento de un raw existente desde el pipeline sin re-scrapear, equivalente a `--reprocess` en modo `--job`
- `src/main.py` `_load_pipeline()`: logea nombre y descripcion del pipeline al cargarlo; soporta `enabled`, `reprocess` y params como dict nativo

### CLI
```bash
# Antes (eliminado)
python -m src.main --job viviendas_adonde --params "pais=peru&pagina=2"
python -m src.main --job viviendas_adonde --no-params

# Ahora: params en el pipeline YAML con tipos nativos
# config/pipelines/mi_pipeline.yaml:
#   jobs:
#     - name: viviendas_adonde
#       params:
#         pais: peru
#         pagina: 2
python -m src.main --pipeline config/pipelines/mi_pipeline.yaml
```

## [0.34.0] - 2026-03-23

### Fixed
- `src/books_to_scrape/process.py`, `src/viviendas_adonde/process.py`: `select_dtypes(include=["object", "str"])` — `"str"` no es un dtype valido en pandas y era ignorado silenciosamente; corregido a `"string"` (el dtype correcto para `pd.StringDtype`)
- `src/shared/job_runner.py`: `cleanup_raw()` se ejecutaba dentro de `_run_full()`, antes de que `_save_output()` guardara el output final; si `_save_output()` fallaba (disco lleno, permisos, etc.) el raw ya habia sido eliminado y los datos se perdian sin posibilidad de recuperacion; `cleanup_raw()` movido a `run()` y ejecutado despues de `_save_output()` — nuevo orden garantizado: `scrape → save_raw → process → save_data → cleanup_raw`
- `src/shared/storage.py` `cleanup_raw()`: con `keep_last_n: 0` no se eliminaba ningun archivo — `files[:-0]` en Python es `files[:0]` que retorna lista vacia; añadido caso explicito `if value == 0: files_to_delete = list(files)`
- `src/shared/job_runner.py` `_run_full()`: el sufijo retornado por `save_raw()` era descartado; ahora se captura y se loguea con el mensaje `"Si el proceso falla, puedes reprocesar con: --reprocess <sufijo>"` para facilitar recuperacion manual
- `src/main.py`: `logger = logging.getLogger(__name__)` creaba el logger `"__main__"` al ejecutar con `python -m src.main`, que propaga al logger raiz en lugar de a `"src"`; los mensajes del orquestador desaparecian silenciosamente; corregido con nombre explicito `logging.getLogger("src.main")`

### Changed
- `src/shared/storage.py` `save_raw()`: firma cambiada de `list[dict]` a `pd.DataFrame` — el DataFrame se construye ahora una sola vez en `_run_full()` y se reutiliza tanto para `save_raw()` como para el procesamiento posterior, eliminando una construccion redundante de DataFrame sobre los mismos datos
- `src/shared/storage.py` `_read_df()`: eliminado `dtype=str` de `pd.read_json()` — el parametro no previene la inferencia de tipos numericos en pandas (bug conocido); la conversion a string la realiza el `.astype(str)` posterior, que es la unica llamada efectiva; añadido comentario explicativo
- `src/shared/job_runner.py` `_run_full()`: el DataFrame string-first se construye antes de llamar a `save_raw()` y se pasa directamente, eliminando la segunda construccion `pd.DataFrame(datos)` que existia anteriormente

### Added
- `src/main.py` `--no-params`: nuevo flag CLI exclusivo de `--job` que ejecuta el job sin parametros y limpia el estado persistido en `.state/<job>_params.json`; mutuamente excluyente con `--params`
- `src/main.py` `_setup_console_handler()`: configura un handler de consola en el logger `"src"` al inicio de `main()` para capturar mensajes del orquestador (serie, pipeline) antes de que el primer job arranque; `setup_logger()` de cada job reemplaza este handler
- `src/main.py`: mensajes del orquestador (`_run_series`, `_load_pipeline`, `_load_job_parts`) migrados de `print()` a `logger.info/error/warning` para que queden registrados en los archivos de log cuando el orquestador se ejecuta en entornos automatizados (CI/CD, cron); `print()` se mantiene exclusivamente para la salida de `--list`

### CLI
```bash
# Ejecutar sin parametros y limpiar estado persistido
python -m src.main --job books_to_scrape --no-params
```

## [0.33.0] - 2026-03-19

### Removed
- `src/<job>/app_job.py`: eliminado de todos los jobs — era boilerplate puro de 12 lineas identicas por job; `main.py` ahora importa directamente `scraper`, `process` y `settings` de cada job sin intermediario

### Changed
- `src/main.py` `get_available_jobs()`: el marker de descubrimiento cambia de `app_job.py` a `scraper.py` — cualquier carpeta en `src/` con un `scraper.py` es reconocida como job valido
- `src/main.py` `_load_job_module()`: reemplazada por `_load_job_parts(job_name)` que retorna la tupla `(scrape_fn, process_fn, settings)` e importa los tres modulos directamente; `main.py` pasa las partes a `job_runner.run()` sin pasar por `app_job`
- `src/main.py`: eliminados `import os` e `import types`; modulo unificado a `pathlib.Path` exclusivamente
- `src/shared/job_runner.py` `_run_full()`: eliminado el ciclo `save_raw → load_raw` — tras guardar el raw, la normalizacion string-first se aplica en memoria con `pd.DataFrame(datos).fillna("").astype(str)`; `load_raw` queda exclusivo para el flujo `--reprocess`; se elimina un ciclo completo de I/O a disco en cada ejecucion normal

## [0.32.0] - 2026-03-19

### Changed
- Estructura: `settings.py` y `web_config.yaml` de cada job movidos de `config/<job>/` a `src/<job>/` — cada job es ahora completamente autocontenido; `config/` queda exclusivamente con `global_settings.py` y `pipelines/`
- `src/shared/job_runner.py` `load_web_config()`: ruta actualizada de `config/<job>/web_config.yaml` a `src/<job>/web_config.yaml`
- `src/<job>/app_job.py`: import de settings actualizado de `from config.<job> import settings` a `from src.<job> import settings`
- Estado en runtime (`last_params`): los archivos de params persistidos se mueven de `config/<job>/last_params.json` a `.state/<job>_params.json`; `.state/` esta en `.gitignore` y se crea automaticamente si no existe — el directorio `config/` queda libre de archivos generados en runtime
- Tests renombrados: `tests/<job>/test_config.py` → `tests/<job>/test_<job>.py` para que el nombre refleje el job que se testea (`test_books_to_scrape.py`, `test_viviendas_adonde.py`)

### Removed
- `src/__pycache__/`: archivos `.pyc` huerfanos de una estructura anterior eliminados

## [0.31.0] - 2026-03-19

### Changed
- `src/shared/storage.py` `load_raw()`: firma simplificada — eliminados parametros `filename` y `extension` que ya estaban disponibles dentro de `raw_config`; nueva firma: `load_raw(suffix, raw_config, data_config)`
- `src/shared/driver_config.py`: clase `DriverConfig` reemplazada por funcion `create_driver(config: dict) -> Driver` — la clase se instanciaba exclusivamente para llamar `.get_driver()` de inmediato y nunca se reutilizaba; la funcion directa elimina el patron `DriverConfig(**config).get_driver()`
- `src/shared/storage.py`: modulo unificado a `pathlib.Path`; eliminados todos los usos de `os.path`, `os.makedirs`, `os.listdir`, `os.remove` y `os.path.isdir`
- `src/shared/storage.py` `build_filepath()`: eliminado `os.makedirs` como efecto secundario — una funcion que construye rutas no debe crear directorios; los directorios se crean ahora en `save_data()` y `save_raw()` inmediatamente antes de escribir; tipo de retorno cambiado de `str` a `Path`
- `config/<job>/settings.py` `PIPELINE_CONFIG`: dict de una sola clave reemplazado por variable directa `SKIP_PROCESS: bool`; acceso simplificado de `settings.PIPELINE_CONFIG.get("skip_process", False)` a `settings.SKIP_PROCESS`

### Refactor
- `src/shared/storage.py` `_parse_raw_timestamp()`: extraida de funcion anidada dentro de `cleanup_raw()` a funcion privada a nivel de modulo; mismo comportamiento, mas legible y testeable de forma independiente

## [0.30.0] - 2026-03-19

### Added
- `src/main.py`: tres nuevos modos de ejecucion en serie que coexisten con `--job`:
  - `--jobs job1,job2,...`: ejecuta una lista de jobs especificos separados por coma
  - `--all`: descubre y ejecuta todos los jobs disponibles en `src/` en orden alfabetico
  - `--pipeline config/pipelines/mi_pipeline.yaml`: ejecuta un pipeline nombrado definido en YAML con params opcionales por job
- `src/main.py` `_run_series()`: funcion interna que itera la lista de jobs, ejecuta cada uno con sus params, captura errores por job sin abortar la serie y muestra un resumen final (`Serie finalizada: N/N jobs exitosos`)
- `src/main.py` `_make_args()`: construye el `Namespace` de args para cada job individual dentro de una serie, desacoplando el contexto de ejecucion de la serie del contexto de cada job
- `src/main.py` `_load_job_module()`: centraliza la importacion dinamica del modulo `app_job` con mensaje de error descriptivo; elimina la duplicacion que existia entre el flujo de `--job` y el nuevo flujo de series
- `src/main.py` `_load_pipeline()`: carga y valida un YAML de pipeline; valida existencia del archivo, presencia de clave `jobs` y campo `name` por job; retorna lista de entradas normalizadas
- `config/pipelines/diario.yaml`: pipeline de ejemplo con ambos jobs y sus params; sirve como plantilla para crear pipelines propios

### Changed
- `src/main.py`: los cuatro modos (`--job`, `--jobs`, `--all`, `--pipeline`) son mutuamente excluyentes via `add_mutually_exclusive_group()`; `--reprocess` y `--params` se validan explicitamente y solo se aceptan junto a `--job`
- `src/main.py`: en modo `--jobs` y `--all` cada job carga automaticamente su propio `last_params.json`; en modo `--pipeline` los params del YAML se pasan directamente al job y se persisten en `last_params.json` para ejecuciones futuras

### CLI
```bash
# Job individual (sin cambios)
python -m src.main --job books_to_scrape
python -m src.main --job books_to_scrape --params "categoria=mystery"
python -m src.main --job books_to_scrape --reprocess 20260319_202702

# Subset especifico en serie
python -m src.main --jobs books_to_scrape,viviendas_adonde

# Todos los jobs en serie
python -m src.main --all

# Pipeline nombrado con params por job
python -m src.main --pipeline config/pipelines/diario.yaml
```

### Architecture
- `--params` no esta soportado con `--jobs`, `--all` ni `--pipeline` — en series cada job resuelve sus params desde `last_params.json`; en pipelines los params se definen en el YAML por job
- Un job que falla en una serie no detiene los siguientes; el error se registra y la ejecucion continua
- El YAML de pipeline es la unica fuente que puede sobreescribir `last_params.json` durante una ejecucion en serie

## [0.29.0] - 2026-03-19

### Fixed
- `src/shared/storage.py` `_write_df()`: añadido parametro `stringify: bool = False` — antes la funcion aplicaba `df.fillna("").astype(str)` incondicionalmente, convirtiendo a string todos los valores incluyendo los del output final; ahora solo `save_raw()` llama con `stringify=True`, mientras `save_data()` usa el default `False` y preserva los tipos que `process.py` asigno (`float`, `int`, etc.); en JSON, `Precio_GBP` se guarda como `51.77` en lugar de `"51.77"` y en XLSX las celdas numericas mantienen su tipo
- `src/shared/job_runner.py` `_run_full()`: `cleanup_raw()` movido fuera del bloque `finally` — cuando `process_fn()` lanzaba una excepcion, el bloque `finally` eliminaba el archivo raw antes de que el usuario pudiera investigar o usar `--reprocess`; ahora `cleanup_raw()` solo se ejecuta si `process()` termina correctamente, preservando el raw ante fallos para permitir reprocesamiento sin re-scrapear
- `src/shared/logger.py` `setup_logger()`: el timestamp del log ahora es el mismo `now` que se usa para nombrar los archivos raw y output — antes `setup_logger` capturaba su propio `datetime.now()` internamente, generando una diferencia de segundos respecto al timestamp de los archivos en ejecuciones lentas; el `now` se captura una unica vez en `run()` y se propaga a `setup_logger`, `save_raw` y `save_data`

### Changed
- `src/shared/job_runner.py` `run()`: `now = datetime.now()` movido antes de `setup_logger()` — `now` es ahora el unico timestamp de referencia de toda la ejecucion y se pasa explicitamente a `setup_logger(job_name, now, **LOG_CONFIG)`
- `src/shared/logger.py` `setup_logger()`: nueva firma `setup_logger(job_name, now, log_folder, level)` — `now: datetime` es el segundo parametro posicional; el log de cada ejecucion (`<job>_YYYYMMDD_HHMMSS.log`) comparte timestamp exacto con los archivos raw y output generados en esa misma ejecucion

## [0.28.0] - 2026-03-19

### Added
- `src/shared/job_runner.py` `_save_last_params()`: persiste el dict de params en `config/<job>/last_params.json` cada vez que se pasa `--params` por CLI
- `src/shared/job_runner.py` `_load_last_params()`: carga los params del archivo persistido si existe; retorna dict vacio si no existe aun
- `config/<job>/last_params.json`: archivo generado automaticamente por el sistema al usar `--params` por primera vez en un job; no requiere creacion manual

### Changed
- `src/shared/job_runner.py` `run()`: logica de resolucion de params — si se pasa `--params` se parsea y se persiste; si no se pasa se cargan los de la ultima ejecucion; permite ejecutar el job repetidas veces sin reescribir los params y cambiarlos solo cuando sea necesario

### CLI
```bash
# Primera vez: define y guarda los params
python -m src.main --job books_to_scrape --params "categoria=mystery&pagina=2"

# Siguientes ejecuciones: recuerda los params anteriores automaticamente
python -m src.main --job books_to_scrape
python -m src.main --job books_to_scrape

# Cuando cambien: pisa los params guardados
python -m src.main --job books_to_scrape --params "categoria=romance&pagina=1"
```

## [0.27.0] - 2026-03-19

### Added
- `src/main.py`: nuevo argumento CLI `--params` — acepta un string en formato `"clave=valor&clave2=valor2"` que se parsea a dict y se propaga al scraper del job indicado; opcional y retrocompatible (jobs sin params siguen funcionando sin cambios)
- `src/shared/job_runner.py` `_parse_params()`: nueva funcion que convierte el string de `--params` en `dict` usando `split("=", 1)` para cada par separado por `&`; retorna dict vacio si `--params` no se paso; lanza `ValueError` con mensaje descriptivo si el formato es invalido
- `src/books_to_scrape/scraper.py` y `src/viviendas_adonde/scraper.py`: firma actualizada de `scrape(driver, web_config)` a `scrape(driver, web_config, params=None)` — el scraper recibe el dict de parametros y puede usarlos para filtrar URLs, ajustar selectores o cualquier logica dependiente del contexto

### Changed
- `src/shared/job_runner.py` `_run_full()`: nuevo parametro `params: dict` que se propaga a `scrape_fn(driver, web_config, params)`; si `params` no esta vacio se registra en el log al inicio de la ejecucion
- `src/shared/job_runner.py` `run()`: parsea `args.params` con `_parse_params()` antes de llamar al flujo correspondiente; en modo `--reprocess` los params se ignoran (el scraper no se ejecuta)

### CLI
```bash
# Sin parametros (comportamiento anterior)
python -m src.main --job viviendas_adonde

# Con parametros
python -m src.main --job viviendas_adonde --params "fecha=01/12/2024&pais=peru"
python -m src.main --job books_to_scrape --params "categoria=mystery&pagina=2"
```

### Architecture
- `params` es exclusivo del scraper: `process()` no los recibe porque opera sobre el DataFrame ya construido; si el scraper necesita anotar el contexto de ejecucion en los datos, puede incluirlos como campo en cada registro
- Los parametros son siempre `str`: la conversion de tipos es responsabilidad del scraper que los consume, consistente con el lineamiento string-first del proyecto
- `&` y `=` son caracteres reservados del formato y no pueden aparecer en valores

## [0.26.0] - 2026-03-19

### Fixed
- `src/books_to_scrape/process.py` y `src/viviendas_adonde/process.py`: `select_dtypes(include=["object"])` revertido a `include=["object", "str"]` — en pandas 4, `StringDtype` ya no queda capturado bajo `"object"` solo; con la forma explicita se procesan ambos tipos sin warning de deprecacion
- `src/shared/storage.py` `save_raw()`: añadida validacion de formato antes de acceder a `data_config[format]` — sin ella, un formato invalido en `raw_config` lanzaba `KeyError` sin mensaje descriptivo, a diferencia de `save_data()` que ya validaba correctamente con `ValueError`
- `tests/books_to_scrape/test_config.py` y `tests/viviendas_adonde/test_config.py`: `test_storage_config_output_folder_exists` renombrado a `test_storage_config_output_folder_is_valid_path` y reescrito para validar que el valor es una cadena no vacia en lugar de verificar existencia en disco — la carpeta de salida se crea en la primera ejecucion del pipeline (`build_filepath` hace `os.makedirs`), por lo que el test fallaba siempre en un repo recien clonado
- `src/shared/job_runner.py` `_run_full()`: `cleanup_raw()` movido a bloque `finally` — si `process_fn` lanzaba una excepcion, la limpieza se omitia y los archivos raw se acumulaban indefinidamente ignorando la politica de retencion configurada
- `tests/books_to_scrape/test_config.py` y `tests/viviendas_adonde/test_config.py`: imports movidos al bloque de imports del modulo — estaban colocados despues de definiciones de funciones, violando PEP 8 y confundiendo linters y formatters

### Changed
- `src/books_to_scrape/process.py` y `src/viviendas_adonde/process.py`: `df = df.copy()` añadido al inicio de `process()` — la funcion mutaba el DataFrame de entrada directamente, violando el contrato de funcion pura que garantiza que el caller no vera cambios inesperados en el objeto que paso
- `src/shared/storage.py` `_read_df()` formato `json`: `.astype(str)` aplicado tras `pd.read_json()` — el parametro `dtype=str` en `read_json` no es confiable en todas las versiones de pandas (columnas numericas pueden persistir como `int64` o `float64`), rompiendo el lineamiento string-first en el raw
- `src/shared/storage.py` `_read_df()` formato `xml`: añadido `encoding=config.get("encoding", "utf-8")` a `pd.read_xml()` — el encoding global de `DATA_CONFIG` se respetaba para CSV y JSON pero se ignoraba para XML
- `src/shared/logger.py`: `logger.propagate = False` añadido tras configurar el logger `"src"` — sin esto, si el root logger de Python tenia handlers activos (por ejemplo en entornos de CI o con `logging.basicConfig()`), los mensajes aparecian duplicados en consola
- `src/shared/storage.py` `cleanup_raw()`: funciones `_extract_timestamp` y `_parse_timestamp` unificadas en una sola `_parse_timestamp` — ambas extraian el sufijo `YYYYMMDD_HHMMSS` del nombre del archivo usando estrategias distintas (`rsplit` vs `split[-2:]`); ahora existe un unico helper y el ordenamiento usa `key=lambda f: _parse_timestamp(f) or datetime.min`

## [0.25.0] - 2026-03-14

### Fixed
- `src/shared/logger.py`: nombre del archivo de log cambiado de `<job>_YYYYMMDD.log` a `<job>_YYYYMMDD_HHMMSS.log` — con solo la fecha, multiples ejecuciones en el mismo dia mezclaban sus logs en el mismo archivo sin separacion; ahora cada ejecucion genera su propio archivo
- `src/shared/storage.py` `_write_df()`: reemplazado `df.astype(str).replace("nan", "")` por `df.fillna("").astype(str)` — el enfoque anterior convertia primero todo a string y luego buscaba el literal `"nan"`, corrompiendo cualquier campo de texto que contuviera esa palabra; ahora los `NaN` reales se rellenan con `""` antes de convertir, preservando el string `"nan"` como dato valido
- `src/shared/storage.py` `cleanup_raw()`: ordenacion de archivos raw cambiada de `key=lambda f: os.path.basename(f)` a una funcion `_extract_timestamp()` que extrae el sufijo `YYYYMMDD_HHMMSS` via `rsplit("_", 2)` — la ordenacion alfabetica del nombre completo era fragil si el campo `filename` contenia guiones bajos adicionales; ahora ordena cronologicamente por el timestamp del sufijo
- `src/shared/storage.py` `cleanup_raw()`: eliminacion de archivos raw envuelta en `try/except OSError` — antes, un archivo bloqueado o sin permisos propagaba la excepcion y cancelaba la ejecucion completa aunque los datos ya se hubieran guardado; ahora emite un `WARNING` y continua con el resto de archivos
- `src/shared/driver_config.py` `get_driver()`: inicializacion del driver envuelta en `try/except Exception` con mensaje accionable que indica verificar Chrome y el puerto; configuracion de ventana (`set_window_size` / `maximize_window`) tambien protegida con `try/except`, que llama a `driver.quit()` antes de relanzar para evitar procesos Chrome huerfanos

### Changed
- `src/shared/job_runner.py` `_run_full()`: llamada a `load_raw()` deduplicada — antes se repetia identicamente en ambas ramas del `if skip_process`, con la diferencia de que una la envolvia en `pd.DataFrame` y la otra no; ahora se llama una sola vez a `raw_records = load_raw(...)` y se bifurca solo en que hacer con los datos (`processed = raw_records` o `processed = process_fn(pd.DataFrame(raw_records))`)

## [0.24.0] - 2026-03-13

### Fixed
- `src/shared/logger.py`: el guard `if logger.handlers: return` reemplazado por un loop que cierra y elimina todos los handlers existentes antes de agregar los nuevos — con el guard anterior, el segundo job ejecutado en el mismo proceso heredaba los handlers del primero (incluido su `FileHandler`), escribiendo sus logs en el archivo del job anterior en lugar del propio
- `src/shared/storage.py` `save_raw()`: nuevo parametro opcional `now: datetime | None = None` — antes generaba su propio `datetime.now()` internamente, desincronizado del `now` usado en `save_data()`; ahora recibe el mismo instante que el output, garantizando coherencia de timestamps entre el archivo raw y los archivos de salida de una misma ejecucion

### Changed
- `src/shared/job_runner.py` (nuevo): toda la logica comun de `app_job.py` extraida a este modulo compartido — `load_web_config()`, `_run_full()`, `_run_reprocess()`, `_save_output()` y `run()`; el `now` se captura una unica vez en `run()` y se propaga a `_run_full()` (para `save_raw`) y a `_save_output()` (para `save_data`)
- `src/<job>/app_job.py`: reducido de 149 lineas a 11 — solo declara los tres imports especificos del job (`scraper`, `process`, `settings`) y delega en `job_runner.run()`; el flujo ETL ya no requiere duplicacion al añadir nuevos jobs
- `src/shared/utils.py` (nuevo): `safe_get_text()` y `safe_get_attr()` movidas aqui desde los `utils.py` de cada job, eliminando la duplicacion; cada job importa las funciones compartidas y conserva su propio `parse_record()` con la logica especifica de extraccion
- `src/<job>/utils.py`: reducido a solo `parse_record()` mas el import desde `src.shared.utils`; los tests y scrapers existentes no requieren cambios (las funciones siguen exportandose desde el namespace del job)
- `tests/<job>/test_config.py`: import de `load_web_config` actualizado de `src.<job>.app_job` a `src.shared.job_runner` con wrapper local que inyecta el `job_name` del job correspondiente

### Architecture
- Un nuevo job requiere exactamente 5 archivos: `app_job.py` (11 lineas), `scraper.py`, `process.py`, `utils.py` y `config/<job>/settings.py` + `web_config.yaml` — sin tocar ningun modulo del framework
- La logica ETL vive en un unico lugar (`job_runner.py`): un bug fix o mejora al pipeline se aplica automaticamente a todos los jobs existentes y futuros
- `safe_get_text` y `safe_get_attr` tienen una sola definicion en el proyecto; cualquier mejora a estas funciones se propaga a todos los jobs

## [0.23.0] - 2026-03-13

### Added
- Nuevo job `books_to_scrape`: scraper para `http://books.toscrape.com/` que extrae Titulo, Precio y Rating de la primera pagina (~20 libros)
- `src/books_to_scrape/utils.py`: nueva funcion `safe_get_attr(element, xpath, attr, fallback)` para extraer atributos HTML en lugar de texto, necesaria para el titulo (atributo `@title` del `<a>`) y el rating (atributo `@class` del `<p>`)
- `src/books_to_scrape/process.py`: transformaciones especificas del job:
  - `Precio_GBP`: extrae el valor numerico del precio (ej: `"£51.77"` → `51.77` como float)
  - `Rating_Numerico`: mapea el rating textual a entero (ej: `"star-rating Three"` → `3`)
- `tests/books_to_scrape/test_config.py`: suite de 28 tests que incluye `TestProcess` y `TestUtils` — clases no presentes en viviendas_adonde — con tests unitarios para las transformaciones de `process.py` y los helpers de `utils.py` usando mocks de WebElement
- `config/books_to_scrape/settings.py`: `undetected=False` (sitio de practica sin anti-bot), salida en CSV y JSON
- `config/books_to_scrape/web_config.yaml`: URL, selectores XPath para container, Titulo, Precio y Rating; `after_load=1s` al ser sitio estatico
- Carpeta `output/books_to_scrape/` creada para almacenar los archivos de salida

### Changed
- `src/books_to_scrape/scraper.py`: usa `driver.open()` en lugar de `uc_open_with_reconnect()` ya que el driver no esta en modo UC (`undetected=False`)
- `src/books_to_scrape/utils.py`: `parse_record()` con logica especifica por campo: extrae `@title` para Titulo, `@class` para Rating y `.text` directo para Precio

### Fixed
- `src/books_to_scrape/process.py`: `select_dtypes(include="object")` corregido a `select_dtypes(include=["object", "str"])` para evitar `Pandas4Warning` de deprecacion

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
