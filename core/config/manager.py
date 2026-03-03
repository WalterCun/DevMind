from pathlib import Path
from typing import Optional
import json
from datetime import datetime

from .schema import AgentConfig


class ConfigManager:
    """Gestiona la configuración del agente"""

    CONFIG_DIR = Path.home() / ".devmind"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    def __init__(self):
        self._config: Optional[AgentConfig] = None
        self._load_config()

    def _load_config(self):
        """Carga configuración desde archivo"""
        if self.CONFIG_FILE.exists():
            with open(self.CONFIG_FILE, 'r') as f:
                data = json.load(f)
                self._config = AgentConfig(**data)
        else:
            self._config = None

    def get_config(self) -> Optional[AgentConfig]:
        """Obtiene la configuración actual"""
        return self._config

    def is_initialized(self) -> bool:
        """Verifica si el wizard fue completado"""
        return self._config is not None and self._config.initialized

    def update_config(self, **kwargs):
        """Actualiza configuración parcial"""
        if not self._config:
            raise ValueError("Configuración no inicializada")

        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self._config.updated_at = datetime.now()
        self._save_config()

    def _save_config(self):
        """Guarda configuración en archivo"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(self._config.dict(), f, indent=2, default=str)

    def reset_config(self):
        """Resetea configuración a valores por defecto"""
        if self.CONFIG_FILE.exists():
            self.CONFIG_FILE.unlink()
        self._config = None