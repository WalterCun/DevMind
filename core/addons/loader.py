# devmind-core/core/addons/loader.py
"""
Cargador dinámico de addons.

Permite cargar, recargar y descargar addons
en tiempo de ejecución sin reiniciar el sistema.
"""

import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from .registry import AddonRegistry
from .base import BaseAddon, AddonManifest

logger = logging.getLogger(__name__)


class AddonLoader:
    """
    Cargador dinámico de addons.

    Características:
    - Carga en caliente (hot-reload)
    - Detección de cambios en archivos
    - Recarga automática opcional
    - Logging detallado
    """

    def __init__(self):
        self.registry = AddonRegistry()
        self._watch_paths: List[Path] = []
        self._last_modified: Dict[str, float] = {}

    def watch_directory(self, path: Path) -> None:
        """Agrega un directorio para monitoreo de cambios"""
        if path not in self._watch_paths:
            self._watch_paths.append(path)
            logger.info(f"Watching directory for addons: {path}")

    def check_for_changes(self) -> List[str]:
        """Verifica si hay addons nuevos o modificados"""
        changed = []

        for watch_path in self._watch_paths:
            if not watch_path.exists():
                continue

            for item in watch_path.iterdir():
                if not item.is_dir() or item.name.startswith("_"):
                    continue

                module_file = item / f"{item.name}.py"
                if not module_file.exists():
                    continue

                mtime = module_file.stat().st_mtime
                addon_name = item.name

                # Verificar si es nuevo o modificado
                if addon_name not in self._last_modified:
                    changed.append(addon_name)
                    logger.info(f"New addon detected: {addon_name}")
                elif mtime > self._last_modified[addon_name]:
                    changed.append(addon_name)
                    logger.info(f"Addon modified: {addon_name}")

                self._last_modified[addon_name] = mtime

        return changed

    def load_new_addons(self) -> int:
        """Carga addons nuevos o modificados"""
        changed = self.check_for_changes()
        loaded = 0

        for addon_name in changed:
            # Si ya existe, recargar
            if addon_name in self.registry._addons:
                self.reload_addon(addon_name)
            else:
                # Cargar nuevo
                self.registry.load_from_directory()

            loaded += 1

        return loaded

    def reload_addon(self, name: str) -> bool:
        """Recarga un addon existente"""
        addon = self.registry.get(name)

        if not addon:
            logger.error(f"Addon '{name}' not found for reload")
            return False

        was_active = addon.active

        # Desactivar
        if was_active:
            self.registry.deactivate(name)

        # Recargar módulo
        try:
            import importlib
            module = sys.modules.get(name)
            if module:
                importlib.reload(module)

            logger.info(f"Reloaded addon: {name}")

            # Reactivar si estaba activo
            if was_active:
                self.registry.activate(name)

            return True

        except Exception as e:
            logger.error(f"Failed to reload addon '{name}': {e}")
            return False

    def get_watched_directories(self) -> List[str]:
        """Obtiene lista de directorios monitoreados"""
        return [str(p) for p in self._watch_paths]

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del loader"""
        return {
            "watched_directories": len(self._watch_paths),
            "tracked_addons": len(self._last_modified),
            "registry_stats": self.registry.get_stats()
        }