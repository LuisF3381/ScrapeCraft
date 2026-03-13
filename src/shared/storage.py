import logging
import os
from datetime import datetime, timedelta
import pandas as pd

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers privados de lectura / escritura (no usar directamente)
# ---------------------------------------------------------------------------

def _write_df(df: pd.DataFrame, filepath: str, format: str, config: dict) -> None:
    """Escribe un DataFrame en el formato indicado usando la config correspondiente."""
    df = df.astype(str).replace("nan", "")
    if format == "csv":
        df.to_csv(filepath, index=False, encoding=config.get("encoding", "utf-8"), sep=config.get("separator", ","))
    elif format == "json":
        df.to_json(filepath, orient=config.get("orient", "records"), indent=config.get("indent", 2), force_ascii=config.get("force_ascii", False))
    elif format == "xml":
        df.to_xml(filepath, index=False, root_name=config.get("root", "registros"), row_name=config.get("row", "registro"))
    elif format == "xlsx":
        df.to_excel(filepath, index=config.get("index", False), sheet_name=config.get("sheet_name", "Datos"))
    else:
        raise ValueError(f"Formato no soportado: {format}")


def _read_df(filepath: str, format: str, config: dict) -> pd.DataFrame:
    """Lee un archivo en el formato indicado usando la config correspondiente."""
    if format == "csv":
        df = pd.read_csv(filepath, encoding=config.get("encoding", "utf-8"), sep=config.get("separator", ","), dtype=str)
    elif format == "json":
        df = pd.read_json(filepath, orient=config.get("orient", "records"), dtype=str)
    elif format == "xml":
        df = pd.read_xml(filepath, dtype=str)
    elif format == "xlsx":
        df = pd.read_excel(filepath, dtype=str)
    else:
        raise ValueError(f"Formato no soportado: {format}")
    return df


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------

def build_filepath(storage_config: dict, format: str, now: datetime | None = None) -> str:
    """
    Construye la ruta del archivo segun el modo de nombrado configurado.

    Args:
        storage_config: Diccionario con configuracion de almacenamiento
        format: Formato de salida (csv, json, xml, xlsx)
        now: Momento de referencia para el nombre del archivo. Si es None se usa datetime.now().
             Pasar el mismo valor a todas las llamadas de un mismo run garantiza nombres coherentes.

    Returns:
        str: Ruta completa del archivo a guardar
    """
    output_folder: str = storage_config["output_folder"]
    filename: str = storage_config["filename"]
    naming_mode: str = storage_config["naming_mode"]

    os.makedirs(output_folder, exist_ok=True)

    now = now or datetime.now()
    date_str: str = now.strftime("%Y%m%d")
    timestamp_str: str = now.strftime("%Y%m%d_%H%M%S")

    if naming_mode == "overwrite":
        filepath = os.path.join(output_folder, f"{filename}.{format}")
    elif naming_mode == "date_suffix":
        filepath = os.path.join(output_folder, f"{filename}_{date_str}.{format}")
    elif naming_mode == "timestamp_suffix":
        filepath = os.path.join(output_folder, f"{filename}_{timestamp_str}.{format}")
    elif naming_mode == "date_folder":
        folder_path = os.path.join(output_folder, date_str)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, f"{filename}.{format}")
    else:
        raise ValueError(f"Modo de nombrado no soportado: {naming_mode}")

    return filepath


def save_data(datos: list[dict], format: str, data_config: dict, storage_config: dict, now: datetime | None = None) -> None:
    """
    Guarda los datos en el formato y ubicacion especificados.

    Args:
        datos:          Lista de diccionarios con los datos a guardar
        format:         Formato de salida (csv, json, xml, xlsx)
        data_config:    Diccionario con configuraciones de cada formato
        storage_config: Diccionario con configuracion de almacenamiento
        now:            Momento de referencia para el nombre del archivo (ver build_filepath)
    """
    if format not in data_config:
        raise ValueError(f"Formato no soportado: {format}. Disponibles: {list(data_config.keys())}")

    filepath: str = build_filepath(storage_config, format, now)
    _write_df(pd.DataFrame(datos), filepath, format, data_config[format])
    logger.info(f"Datos guardados en {filepath} ({len(datos)} registros)")


def save_raw(datos: list[dict], raw_config: dict, data_config: dict) -> str:
    """
    Guarda los datos en bruto con sufijo timestamp en el formato indicado por raw_config.

    Args:
        datos:       Lista de diccionarios con los datos a guardar
        raw_config:  Diccionario con configuracion del raw
        data_config: Diccionario con configuraciones de formato (DATA_CONFIG)

    Returns:
        str: Sufijo timestamp generado (ej: "20260312_143052")
    """
    raw_folder: str = raw_config["raw_folder"]
    filename: str = raw_config["filename"]
    format: str = raw_config["format"]

    os.makedirs(raw_folder, exist_ok=True)

    suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath: str = os.path.join(raw_folder, f"{filename}_{suffix}.{format}")

    _write_df(pd.DataFrame(datos), filepath, format, data_config[format])
    logger.info(f"Raw guardado en {filepath} ({len(datos)} registros)")

    return suffix


def load_raw(filename: str, extension: str, suffix: str, raw_config: dict, data_config: dict) -> list[dict]:
    """
    Lee un archivo raw y lo retorna como lista de diccionarios sin transformaciones.
    Se usa cuando PIPELINE_CONFIG["skip_process"] es True.

    Args:
        filename:    Nombre base del archivo (ej: "viviendas")
        extension:   Extension del archivo   (ej: "csv")
        suffix:      Sufijo timestamp de la ejecucion (ej: "20260312_143052")
        raw_config:  Diccionario con configuracion del raw
        data_config: Diccionario con configuraciones de formato (DATA_CONFIG)

    Returns:
        list[dict]: Datos del raw sin transformar
    """
    filepath: str = os.path.join(raw_config["raw_folder"], f"{filename}_{suffix}.{extension}")
    return _read_df(filepath, extension, data_config[extension]).to_dict(orient="records")


def cleanup_raw(raw_config: dict) -> None:
    """
    Limpia archivos raw segun la politica de retencion configurada.

    Args:
        raw_config: Diccionario con configuracion del raw
    """
    raw_folder: str = raw_config["raw_folder"]
    filename: str = raw_config["filename"]
    format: str = raw_config["format"]
    retention: dict = raw_config.get("retention", {"mode": "keep_all"})
    mode: str = retention.get("mode", "keep_all")

    if mode == "keep_all":
        return

    if not os.path.isdir(raw_folder):
        return

    files: list[str] = sorted(
        [
            os.path.join(raw_folder, f)
            for f in os.listdir(raw_folder)
            if f.startswith(f"{filename}_") and f.endswith(f".{format}")
        ],
        key=lambda f: os.path.basename(f)
    )

    if mode == "keep_last_n":
        value: int = retention["value"]
        files_to_delete: list[str] = files[:-value] if len(files) > value else []
    elif mode == "keep_days":
        value: int = retention["value"]
        cutoff: datetime = datetime.now() - timedelta(days=value)

        def _parse_timestamp(filepath: str) -> datetime | None:
            try:
                stem = os.path.splitext(os.path.basename(filepath))[0]  # "viviendas_20260312_143052"
                ts_str = "_".join(stem.split("_")[-2:])                  # "20260312_143052"
                return datetime.strptime(ts_str, "%Y%m%d_%H%M%S")
            except ValueError:
                logger.warning(f"Archivo con nombre inesperado en raw, ignorando: {os.path.basename(filepath)}")
                return None

        files_to_delete = [f for f in files if (ts := _parse_timestamp(f)) is not None and ts < cutoff]
    else:
        raise ValueError(f"Modo de retencion no soportado: {mode}")

    for filepath in files_to_delete:
        os.remove(filepath)
        logger.info(f"Raw eliminado: {filepath}")
