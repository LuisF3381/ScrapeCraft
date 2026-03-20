"""
Configuracion especifica del job books_to_scrape.
Para configuracion global (logs, formatos) ver config/global_settings.py
"""

# ============================================
# CONFIGURACIÓN DEL DRIVER
# ============================================

DRIVER_CONFIG = {
    # Modo headless: Ejecutar sin interfaz gráfica (útil para producción/servidores)
    "headless": False,

    # Undetected mode: books.toscrape.com es un sitio de practica sin anti-bot
    "undetected": False,

    # Maximizar ventana: Maximizar automáticamente la ventana del navegador
    "maximize": True,

    # Tamaño de ventana: Tupla (ancho, alto) para tamaño específico
    "window_size": None,

    # User agent: User agent personalizado para simular diferentes navegadores
    "user_agent": None,

    # Proxy: Servidor proxy en formato "ip:puerto"
    "proxy": None
}

# ============================================
# CONFIGURACIÓN DE ALMACENAMIENTO
# ============================================

STORAGE_CONFIG = {
    # Carpeta de salida (relativa a la raíz del proyecto)
    "output_folder": "output/books_to_scrape",

    # Nombre base del archivo (sin extensión)
    "filename": "books",

    # Modo de nombrado del archivo:
    # - "overwrite": Sobrescribe el archivo (books.csv)
    # - "date_suffix": Añade fecha al nombre (books_20260130.csv)
    # - "timestamp_suffix": Añade fecha y hora (books_20260130_143052.csv)
    # - "date_folder": Crea subcarpeta con fecha (20260130/books.csv)
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
    "raw_folder": "raw/books_to_scrape",

    # Nombre base del archivo raw (sin extension ni sufijo)
    "filename": "books",

    # Formato del archivo raw: csv | json | xml | xlsx
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
