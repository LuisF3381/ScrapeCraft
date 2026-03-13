import logging
import pandas as pd

logger = logging.getLogger(__name__)


def process(df: pd.DataFrame) -> list[dict]:
    """
    Aplica transformaciones a los datos raw y retorna el resultado procesado.

    Args:
        df: DataFrame con los datos raw a transformar

    Returns:
        list[dict]: Lista de diccionarios con los datos procesados
    """

    # CODIGO IMPLEMENTA DATA ENGINEER

    # --- Inicio del procesamiento ---
    
    # Limpieza de espacios en todas las columnas de texto
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].str.strip()

    # Extraccion del precio numerico (elimina simbolo de moneda, separadores y texto)
    if "Precio" in df.columns:
        df["Precio_Numerico"] = (
            df["Precio"]
            .str.replace(r"[^\d]", "", regex=True)
            .apply(lambda x: int(x) if x else None)
        )

    # --- Fin del procesamiento ---
    logger.info(f"Procesamiento completado: {len(df)} registros")

    return df.to_dict(orient="records")
