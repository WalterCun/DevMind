# devmind-core/core/utils/logger.py
"""
Configuración centralizada de logging para DevMind Core.
"""

import logging
import os
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(
        level: str = None,
        log_file: str = None,
        console_output: bool = None,
        production: bool = False
) -> None:
    """
    Configura logging para toda la aplicación.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Ruta opcional para archivo de log
        console_output: Si mostrar logs en consola
    """
    import os

    # ✅ Leer configuración desde variables de entorno
    is_production = os.getenv("DEVMIND_PRODUCTION", "False").lower() == "true"

    if level is None:
        level = os.getenv("LOG_LEVEL", "WARNING" if is_production else "DEBUG")

    if console_output is None:
        # ✅ En desarrollo (PRODUCCIÓN=False), mostrar logs en consola por defecto
        console_output = os.getenv("LOG_CONSOLE", "True" if not is_production else "False").lower() == "true"

    if log_file is None:
        log_file = os.getenv("LOG_FILE", "~/.devmind/devmind.log")

    # Formato de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Handlers
    handlers = []

    if console_output:
        # Rich handler para consola con colores
        handlers.append(RichHandler(
            rich_tracebacks=True,
            show_level=True,
            show_path=False,
            markup=True,
            level=logging.WARNING if production else logging.DEBUG
        ))

    if log_file:
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(logging.INFO if production else logging.DEBUG)
        handlers.append(file_handler)

    # Configurar root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format if not console_output else None,
        handlers=handlers,
        force=True
    )

    # Silenciar loggers muy verbosos de terceros
    logging.getLogger("chromadb").setLevel(logging.WARNING if production else logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("crewai").setLevel(logging.WARNING if production else logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("posthog").setLevel(logging.ERROR if production else logging.WARNING)

    if not production:
        logging.info(f"🔧 Logging configured: level={level}, console={console_output}, file={log_file}")
