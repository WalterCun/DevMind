# devmind-core/core/utils/logger.py
"""
Configuración centralizada de logging para DevMind Core.
"""

import logging


def setup_logging(
        level: str = None,
        log_file: str = None,
        console_output: bool = None
) -> None:
    """
    Configura logging para toda la aplicación.
    Respeta variables de entorno: DEVMIND_PRODUCTION, LOG_LEVEL, LOG_CONSOLE
    """
    import os

    is_production = os.getenv("DEVMIND_PRODUCTION", "False").lower() == "true"

    if level is None:
        level = os.getenv("LOG_LEVEL", "WARNING" if is_production else "DEBUG")

    if console_output is None:
        console_output = os.getenv("LOG_CONSOLE", "True" if not is_production else "False").lower() == "true"

    if log_file is None:
        log_file = os.getenv("LOG_FILE", "~/.devmind/devmind.log")

    # Formato de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Handlers
    handlers = []

    if console_output:
        # Rich handler para consola con colores
        from rich.logging import RichHandler
        handlers.append(RichHandler(
            rich_tracebacks=True,
            show_level=True,
            show_path=False,
            markup=True,
            level=logging.WARNING if is_production else logging.DEBUG
        ))

    if log_file:
        # File handler
        from pathlib import Path
        log_path = Path(log_file).expanduser()
        log_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_path, encoding='utf-8', mode='a')
        file_handler.setFormatter(logging.Formatter(log_format))
        file_handler.setLevel(logging.INFO if is_production else logging.DEBUG)
        handlers.append(file_handler)

    # Configurar root logger
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=log_format if not console_output else None,
        handlers=handlers,
        force=True  # Reemplazar configuración existente
    )

    logging.getLogger("chromadb").setLevel(logging.WARNING if is_production else logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("crewai").setLevel(logging.WARNING if is_production else logging.INFO)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("posthog").setLevel(logging.ERROR if is_production else logging.WARNING)

    if not is_production:
        logging.info(f"🔧 Logging configured: level={level}, console={console_output}, file={log_file}")
