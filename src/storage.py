import logging
import os
from datetime import datetime
import pandas as pd


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
        datos: Lista de diccionarios con los datos a guardar
        format: Formato de salida (csv, json, xml, xlsx)
        data_config: Diccionario con configuraciones de cada formato
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

    logger: logging.Logger = logging.getLogger("scrapecraft")
    logger.info(f"Datos guardados en {filepath} ({len(datos)} registros)")
