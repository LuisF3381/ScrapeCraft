# =============================================================================
# Consolidador de ejemplo
#
# Un consolidador combina los outputs de multiples jobs en un unico dataset.
# Se activa desde el pipeline YAML con el bloque 'consolidate'.
#
# Para crear tu propio consolidador:
#   1. Copia este archivo a src/consolidadores/<nombre>.py
#   2. Ajusta STORAGE_CONFIG segun tus necesidades
#   3. Implementa la logica en la funcion consolidate()
#   4. Referencia el modulo en el pipeline YAML: consolidate.module: <nombre>
#
# Restriccion: todos los jobs del pipeline deben tener la misma format_config
# para el formato declarado en consolidate.format del YAML.
# =============================================================================

import pandas as pd

# =========================================================================
# ZONA DATA ENGINEER (1/2) — configurar almacenamiento del consolidado
# =========================================================================

STORAGE_CONFIG = {
    # --- Output ---
    "output_folder": "output/consolidados",
    "filename": "consolidado",
    "naming_mode": "date_suffix",      # overwrite | date_suffix | timestamp_suffix | date_folder
    "output_formats": ["csv"],         # formatos en los que se guarda el consolidado

    # --- Configuracion de formatos ---
    # Debe coincidir con la format_config de los jobs para el formato de consolidacion.
    "format_config": {
        "csv": {
            "encoding": "utf-8",
            "separator": ";",
            "index": False
        }
    }
}

# =========================================================================
# FIN ZONA DATA ENGINEER (1/2)
# =========================================================================


def consolidate(job_dataframes: dict[str, pd.DataFrame], params: dict = None) -> list[dict]:
    """
    Combina los outputs de multiples jobs en un unico dataset.

    El framework carga automaticamente los archivos de cada job y los entrega
    como DataFrames listos para usar. El data engineer solo implementa la logica.

    Args:
        job_dataframes: Mapa de job_name -> DataFrame con los datos del job.
                        Ejemplo:
                            books_df    = job_dataframes["books_to_scrape"]
                            viviendas_df = job_dataframes["viviendas_adonde"]
        params:         Parametros opcionales definidos en consolidate.params
                        del pipeline YAML.

    Returns:
        list[dict]: Datos consolidados. Cada dict es un registro del output final.
    """
    # =========================================================================
    # ZONA DATA ENGINEER (2/2) — implementar logica de consolidacion
    # =========================================================================
    params = params or {}

    # --- Desempaquetar DataFrames por job ---
    books_df     = job_dataframes["books_to_scrape"]
    viviendas_df = job_dataframes["viviendas_adonde"]

    # --- Logica de consolidacion (personalizar segun necesidad) ---
    books_df["_fuente"]     = "books_to_scrape"
    viviendas_df["_fuente"] = "viviendas_adonde"

    consolidado = pd.concat([books_df, viviendas_df], ignore_index=True)

    # =========================================================================
    # FIN ZONA DATA ENGINEER (2/2)
    # =========================================================================
    return consolidado.to_dict(orient="records")


def validate(df: pd.DataFrame) -> list[str]:
    """
    Valida el DataFrame consolidado antes de guardarlo.
    Funcion opcional — si no se define, la validacion se omite.
    Retorna una lista de errores encontrados.
    Lista vacia significa que la validacion fue exitosa.

    Args:
        df: DataFrame con los datos consolidados por consolidate()

    Returns:
        list[str]: Lista de mensajes de error. Vacia si la validacion es exitosa.
    """
    errors: list[str] = []

    # =========================================================================
    # ZONA GOBIERNO DE DATOS
    # =========================================================================

    # =========================================================================
    # FIN ZONA GOBIERNO DE DATOS
    # =========================================================================

    return errors
