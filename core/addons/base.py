# devmind-core/core/addons/base.py
"""
Clase base para addons de DevMind Core.

Los addons son extensiones que agregan funcionalidad
al sistema sin modificar el core.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class AddonManifest:
    """Manifiesto de un addon"""
    name: str
    version: str
    description: str
    author: str
    homepage: Optional[str] = None
    license: str = "MIT"
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    agents: List[str] = field(default_factory=list)
    commands: List[str] = field(default_factory=list)
    min_devmind_version: str = "0.1.0"


class BaseAddon(ABC):
    """
    Clase base abstracta para todos los addons.

    Los addons deben implementar:
    - manifest: Información del addon
    - activate(): Se llama al activar el addon
    - deactivate(): Se llama al desactivar el addon
    """

    def __init__(self):
        self.active = False
        self.loaded_at: Optional[datetime] = None
        self.config: Dict[str, Any] = {}

    @property
    @abstractmethod
    def manifest(self) -> AddonManifest:
        """Retorna el manifiesto del addon"""
        pass

    @abstractmethod
    def activate(self) -> bool:
        """
        Activa el addon.

        Returns:
            True si la activación fue exitosa
        """
        pass

    @abstractmethod
    def deactivate(self) -> bool:
        """
        Desactiva el addon.

        Returns:
            True si la desactivación fue exitosa
        """
        pass

    def on_load(self) -> None:
        """Se llama cuando el addon se carga"""
        logger.info(f"Addon loaded: {self.manifest.name} v{self.manifest.version}")

    def on_unload(self) -> None:
        """Se llama cuando el addon se descarga"""
        logger.info(f"Addon unloaded: {self.manifest.name}")

    def get_config(self, key: str, default: Any = None) -> Any:
        """Obtiene configuración del addon"""
        return self.config.get(key, default)

    def set_config(self, key: str, value: Any) -> None:
        """Establece configuración del addon"""
        self.config[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el addon a dict"""
        return {
            "name": self.manifest.name,
            "version": self.manifest.version,
            "description": self.manifest.description,
            "author": self.manifest.author,
            "active": self.active,
            "loaded_at": self.loaded_at.isoformat() if self.loaded_at else None,
            "dependencies": self.manifest.dependencies,
            "tools": self.manifest.tools,
            "agents": self.manifest.agents,
            "commands": self.manifest.commands
        }
