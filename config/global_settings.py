"""
Configuracion global de ScrapeCraft.
Aplica a todos los procesos independientemente del job que se ejecute.
"""
# =========================================================================
# ZONA DATA ENGINEER — modificar en casos excepcionales
# (nivel de log, carpeta de logs)
# La configuracion de formatos (encoding, separadores, etc.) va en
# STORAGE_CONFIG["format_config"] de cada src/<job>/settings.py
# =========================================================================

# ============================================
# CONFIGURACIÓN DE LOGGING
# ============================================

LOG_CONFIG = {
    # Carpeta donde se guardan los logs
    "log_folder": "log",

    # Nivel de logging: DEBUG, INFO, WARNING, ERROR
    "level": "INFO"
}
