"""
Configuracion especifica del job viviendas_adonde.
Para configuracion global (logs) ver config/global_settings.py
"""
# =========================================================================
# ZONA DATA ENGINEER — configurar todos los bloques de este archivo
# =========================================================================

# ============================================
# CONFIGURACIÓN DEL DRIVER
# ============================================

DRIVER_CONFIG = {
    # Modo headless: Ejecutar sin interfaz gráfica (útil para producción/servidores)
    "headless": False,

    # Undetected mode: Activar undetected-chromedriver para evadir detección
    "undetected": True,

    # Maximizar ventana: Maximizar automáticamente la ventana del navegador
    "maximize": True,

    # Tamaño de ventana: Tupla (ancho, alto) para tamaño específico
    # Si se define, tiene prioridad sobre maximize
    "window_size": None,  # Ejemplo: (1920, 1080)

    # User agent: User agent personalizado para simular diferentes navegadores
    "user_agent": None,  # Ejemplo: "Mozilla/5.0 (Windows NT 10.0; Win64; x64)..."

    # Proxy: Servidor proxy en formato "ip:puerto"
    "proxy": None  # Ejemplo: "123.45.67.89:8080"
}

# ============================================
# CONFIGURACIÓN DE ALMACENAMIENTO
# ============================================

STORAGE_CONFIG = {
    # --- Output ---

    # Carpeta de salida (relativa a la raíz del proyecto)
    "output_folder": "output/viviendas_adonde",

    # Nombre base del archivo (sin extensión)
    "filename": "viviendas",

    # Modo de nombrado del archivo:
    # - "overwrite":        Sobrescribe el archivo             (viviendas.csv)
    # - "date_suffix":      Añade fecha al nombre              (viviendas_20260130.csv)
    # - "timestamp_suffix": Añade fecha y hora                 (viviendas_20260130_143052.csv)
    # - "date_folder":      Crea subcarpeta con fecha          (20260130/viviendas.csv)
    "naming_mode": "date_suffix",

    # Formatos de salida: lista de formatos a exportar
    # Opciones disponibles: "csv", "json", "xml", "xlsx"
    # Nota: el primer formato tambien se usa para guardar el raw
    "output_formats": ["csv", "json"],

    # --- Raw ---

    # Carpeta donde se guardan los archivos raw (datos en bruto pre-procesamiento)
    "raw_folder": "raw/viviendas_adonde",

    # Politica de retencion de archivos raw:
    # - "keep_all":    Conserva todos los archivos
    # - "keep_last_n": Conserva los ultimos N archivos
    # - "keep_days":   Conserva los archivos de los ultimos N dias
    "retention": {
        "mode": "keep_last_n",
        "value": 5
    },

    # --- Configuracion de formatos ---

    # Opciones de escritura/lectura para cada formato usado por este job.
    # Define al menos los formatos declarados en output_formats.
    "format_config": {
        "csv": {
            "encoding": "utf-8",
            "separator": ";",
            "index": False
        },
        "json": {
            "indent": 2,
            "force_ascii": False,
            "orient": "records"
        }
    }
}

# ============================================
# CONFIGURACIÓN DEL PIPELINE
# ============================================

# Si es True, omite el paso de process.py y guarda el raw directamente.
SKIP_PROCESS = False
