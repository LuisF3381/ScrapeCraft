import logging
import os
from datetime import datetime
import pandas as pd

logger = logging.getLogger(__name__)


def build_filepath(storage_config: dict, format: str) -> str:
    """
    Construye la ruta del archivo segun el modo de nombrado configurado.

    Args:
        storage_config: Diccionario con configuracion de almacenamiento
        format: Formato de salida (csv, json, xml, xlsx)

    Returns:
        str: Ruta completa del archivo a guardar
    """
    output_folder: str = storage_config["output_folder"]
    filename: str = storage_config["filename"]
    naming_mode: str = storage_config["naming_mode"]
    extension: str = format

    # Garantizamos que la carpeta de salida existe
    os.makedirs(output_folder, exist_ok=True)

    # Obtenemos la fecha actual
    now = datetime.now()
    date_str: str = now.strftime("%Y%m%d")
    timestamp_str: str = now.strftime("%Y%m%d_%H%M%S")

    # Seleccion del modo correspondiente de escritura
    if naming_mode == "overwrite":
        filepath = os.path.join(output_folder, f"{filename}.{extension}")

    elif naming_mode == "date_suffix":
        filepath = os.path.join(output_folder, f"{filename}_{date_str}.{extension}")

    elif naming_mode == "timestamp_suffix":
        filepath = os.path.join(output_folder, f"{filename}_{timestamp_str}.{extension}")

    elif naming_mode == "date_folder":
        folder_path = os.path.join(output_folder, date_str)
        os.makedirs(folder_path, exist_ok=True)
        filepath = os.path.join(folder_path, f"{filename}.{extension}")

    else:
        raise ValueError(f"Modo de nombrado no soportado: {naming_mode}")

    return filepath


def save_data(datos: list[dict], format: str, data_config: dict, storage_config: dict) -> None:
    """
    Guarda los datos en el formato y ubicacion especificados.

    Args:
        datos:          Lista de diccionarios con los datos a guardar
        format:         Formato de salida (csv, json, xml, xlsx)
        data_config:    Diccionario con configuraciones de cada formato
        storage_config: Diccionario con configuracion de almacenamiento
    """
    # Verificamos el formato
    if format not in data_config:
        raise ValueError(f"Formato no soportado: {format}. Disponibles: {list(data_config.keys())}")

    df: pd.DataFrame = pd.DataFrame(datos)
    config: dict = data_config[format]
    filepath: str = build_filepath(storage_config, format)

    # Escritura en el formato correspondiente
    if format == "csv":
        df.to_csv(
            filepath,
            index=config.get("index", False),
            encoding=config.get("encoding", "utf-8"),
            sep=config.get("separator", ",")
        )

    elif format == "json":
        df.to_json(
            filepath,
            orient=config.get("orient", "records"),
            indent=config.get("indent", 2),
            force_ascii=config.get("force_ascii", False)
        )

    elif format == "xml":
        df.to_xml(
            filepath,
            index=False,
            root_name=config.get("root", "registros"),
            row_name=config.get("row", "registro")
        )

    elif format == "xlsx":
        df.to_excel(
            filepath,
            index=config.get("index", False),
            sheet_name=config.get("sheet_name", "Datos")
        )

    else:
        raise ValueError(f"Formato no soportado: {format}")

    logger.info(f"Datos guardados en {filepath} ({len(datos)} registros)")


def save_raw(datos: list[dict], raw_config: dict) -> str:
    """
    Guarda los datos en bruto como CSV con sufijo timestamp.

    Args:
        datos:      Lista de diccionarios con los datos a guardar
        raw_config: Diccionario con configuracion del raw

    Returns:
        str: Sufijo timestamp generado (ej: "20260312_143052")
    """
    raw_folder: str = raw_config["raw_folder"]
    filename: str = raw_config["filename"]

    os.makedirs(raw_folder, exist_ok=True)

    suffix: str = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath: str = os.path.join(raw_folder, f"{filename}_{suffix}.csv")

    df: pd.DataFrame = pd.DataFrame(datos)
    df.to_csv(filepath, index=False, encoding="utf-8")

    logger.info(f"Raw guardado en {filepath} ({len(datos)} registros)")

    return suffix


def load_raw(filename: str, extension: str, suffix: str, raw_config: dict) -> list[dict]:
    """
    Lee un archivo raw y lo retorna como lista de diccionarios sin transformaciones.
    Se usa cuando PIPELINE_CONFIG["skip_process"] es True.

    Args:
        filename:   Nombre base del archivo (ej: "viviendas")
        extension:  Extension del archivo   (ej: "csv")
        suffix:     Sufijo timestamp de la ejecucion (ej: "20260312_143052")
        raw_config: Diccionario con configuracion del raw

    Returns:
        list[dict]: Datos del raw sin transformar
    """
    filepath: str = os.path.join(raw_config["raw_folder"], f"{filename}_{suffix}.{extension}")
    return pd.read_csv(filepath).to_dict(orient="records")


def cleanup_raw(raw_config: dict) -> None:
    """
    Limpia archivos raw segun la politica de retencion configurada.

    Args:
        raw_config: Diccionario con configuracion del raw
    """
    raw_folder: str = raw_config["raw_folder"]
    filename: str = raw_config["filename"]
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
            if f.startswith(f"{filename}_") and f.endswith(".csv")
        ],
        key=os.path.getmtime
    )

    if mode == "keep_last_n":
        value: int = retention["value"]
        files_to_delete: list[str] = files[:-value] if len(files) > value else []

    elif mode == "keep_days":
        value: int = retention["value"]
        cutoff: float = datetime.now().timestamp() - (value * 86400)
        files_to_delete = [f for f in files if os.path.getmtime(f) < cutoff]

    else:
        raise ValueError(f"Modo de retencion no soportado: {mode}")

    for filepath in files_to_delete:
        os.remove(filepath)
        logger.info(f"Raw eliminado: {filepath}")
