# devmind-core/core/utils/logger.py
"""
Configuración centralizada de logging para DevMind Core.
"""

import logging
from pathlib import Path

from rich.logging import RichHandler


def setup_logging(
        level: str = "INFO",
        log_file: str = None,
        console_output: bool = True
) -> None:
    """
    Configura logging para toda la aplicación.

    Args:
        level: Nivel de logging (DEBUG, INFO, WARNING, ERROR)
        log_file: Ruta opcional para archivo de log
        console_output: Si mostrar logs en consola
    """

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
            markup=True
        ))

    if log_file:
        # File handler
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

    # Configurar root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format if not console_output else None,
        handlers=handlers,
        force=True  # Reemplazar configuración existente
    )

    # Silenciar loggers muy verbosos de terceros
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("crewai").setLevel(logging.INFO)

    logging.info(f"🔧 Logging configured: level={level}, console={console_output}, file={log_file}")