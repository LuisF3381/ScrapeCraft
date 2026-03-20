"""
Configuracion especifica del job viviendas_adonde.
Para configuracion global (logs, formatos) ver config/global_settings.py
"""

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
    # Carpeta de salida (relativa a la raíz del proyecto)
    "output_folder": "output/viviendas_adonde",

    # Nombre base del archivo (sin extensión)
    "filename": "viviendas",

    # Modo de nombrado del archivo:
    # - "overwrite": Sobrescribe el archivo (viviendas.csv)
    # - "date_suffix": Añade fecha al nombre (viviendas_20260130.csv)
    # - "timestamp_suffix": Añade fecha y hora (viviendas_20260130_143052.csv)
    # - "date_folder": Crea subcarpeta con fecha (20260130/viviendas.csv)
    "naming_mode": "date_suffix",

    # Formatos de salida: lista de formatos a exportar
    # Opciones disponibles: "csv", "json", "xml", "xlsx"
    "output_formats": ["csv", "json"]
}

# ============================================
# CONFIGURACIÓN DEL PIPELINE
# ============================================

# Si es True, omite el paso de process.py y guarda el raw directamente.
SKIP_PROCESS = False

# ============================================
# CONFIGURACIÓN DE RAW (datos en bruto)
# ============================================

RAW_CONFIG = {
    # Carpeta donde se guardan los archivos raw
    "raw_folder": "raw/viviendas_adonde",

    # Nombre base del archivo raw (sin extension ni sufijo)
    "filename": "viviendas",

    # Formato del archivo raw: csv | json | xml | xlsx
    # Usa automaticamente la configuracion de DATA_CONFIG[format]
    "format": "csv",

    # Politica de retencion de archivos raw:
    # - "keep_all":    Conserva todos los archivos
    # - "keep_last_n": Conserva los ultimos N archivos
    # - "keep_days":   Conserva los archivos de los ultimos N dias
    "retention": {
        "mode": "keep_last_n",
        "value": 5
    }
}
