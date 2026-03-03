# devmind-core/core/addons/registry.py
"""
Registro central de addons para DevMind Core.

Permite registrar, activar, desactivar y gestionar
addons de forma dinámica.
"""

import importlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Type, Any
from datetime import datetime
import json

from .base import BaseAddon, AddonManifest

logger = logging.getLogger(__name__)


class AddonRegistry:
    """
    Registro singleton de addons.

    Características:
    - Registro dinámico de addons
    - Activación/desactivación en caliente
    - Carga automática desde directorios
    - Gestión de dependencias
    - Persistencia de configuración
    """

    _instance: Optional['AddonRegistry'] = None
    _addons: Dict[str, BaseAddon]
    _addons_dir: Path
    _config_file: Path

    def __new__(cls) -> 'AddonRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._addons = {}
            cls._instance._addons_dir = Path.home() / ".devmind" / "addons"
            cls._instance._config_file = cls._instance._addons_dir / "addons_config.json"
            cls._instance._addons_dir.mkdir(parents=True, exist_ok=True)
        return cls._instance

    def register(self, addon: BaseAddon) -> str:
        """Registra un addon"""
        name = addon.manifest.name

        if name in self._addons:
            logger.warning(f"Addon '{name}' already registered, overwriting")

        self._addons[name] = addon
        addon.on_load()

        logger.info(f"Registered addon: {name} v{addon.manifest.version}")
        return name

    def unregister(self, name: str) -> bool:
        """Elimina un addon del registro"""
        if name in self._addons:
            addon = self._addons[name]
            if addon.active:
                addon.deactivate()
            addon.on_unload()
            del self._addons[name]
            logger.info(f"Unregistered addon: {name}")
            return True
        return False

    def activate(self, name: str) -> bool:
        """Activa un addon"""
        addon = self._addons.get(name)

        if not addon:
            logger.error(f"Addon '{name}' not found")
            return False

        if addon.active:
            logger.warning(f"Addon '{name}' is already active")
            return True

        # Verificar dependencias
        if not self._check_dependencies(addon):
            logger.error(f"Addon '{name}' dependencies not met")
            return False

        try:
            success = addon.activate()
            if success:
                addon.active = True
                addon.loaded_at = datetime.now()
                logger.info(f"Activated addon: {name}")
                self._save_config()
            return success
        except Exception as e:
            logger.error(f"Failed to activate addon '{name}': {e}")
            return False

    def deactivate(self, name: str) -> bool:
        """Desactiva un addon"""
        addon = self._addons.get(name)

        if not addon:
            logger.error(f"Addon '{name}' not found")
            return False

        if not addon.active:
            logger.warning(f"Addon '{name}' is already inactive")
            return True

        try:
            success = addon.deactivate()
            if success:
                addon.active = False
                logger.info(f"Deactivated addon: {name}")
                self._save_config()
            return success
        except Exception as e:
            logger.error(f"Failed to deactivate addon '{name}': {e}")
            return False

    def get(self, name: str) -> Optional[BaseAddon]:
        """Obtiene un addon por nombre"""
        return self._addons.get(name)

    def list_addons(
            self,
            active_only: bool = False,
            inactive_only: bool = False
    ) -> List[Dict[str, Any]]:
        """Lista addons con filtros opcionales"""
        addons = []

        for addon in self._addons.values():
            if active_only and not addon.active:
                continue
            if inactive_only and addon.active:
                continue

            addons.append(addon.to_dict())

        return addons

    def get_active_addons(self) -> List[str]:
        """Obtiene lista de addons activos"""
        return [name for name, addon in self._addons.items() if addon.active]

    def load_from_directory(self, directory: Optional[Path] = None) -> int:
        """Carga addons desde un directorio"""
        dir_path = directory or self._addons_dir

        if not dir_path.exists():
            return 0

        loaded = 0
        for item in dir_path.iterdir():
            if not item.is_dir():
                continue

            if item.name.startswith("_"):
                continue

            try:
                # Buscar módulo principal del addon
                module_file = item / f"{item.name}.py"
                if not module_file.exists():
                    continue

                # Importar dinámicamente
                spec = importlib.util.spec_from_file_location(
                    item.name, module_file
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Buscar clase que herede de BaseAddon
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                            isinstance(attr, type) and
                            issubclass(attr, BaseAddon) and
                            attr != BaseAddon
                    ):
                        addon = attr()
                        self.register(addon)
                        loaded += 1
                        logger.info(f"Loaded addon from {item}: {attr_name}")

            except Exception as e:
                logger.error(f"Failed to load addon from {item}: {e}")

        # Cargar configuración guardada y activar addons que estaban activos
        self._load_config()

        return loaded

    def _check_dependencies(self, addon: BaseAddon) -> bool:
        """Verifica que las dependencias del addon estén satisfechas"""
        for dep in addon.manifest.dependencies:
            # Verificar si es un addon requerido
            if dep in self._addons:
                if not self._addons[dep].active:
                    logger.warning(f"Dependency '{dep}' is not active")
                    return False
            else:
                # Verificar si es un paquete Python
                try:
                    importlib.import_module(dep)
                except ImportError:
                    logger.warning(f"Dependency '{dep}' not installed")
                    return False

        return True

    def _save_config(self) -> None:
        """Guarda configuración de addons activos"""
        config = {
            "active_addons": self.get_active_addons(),
            "timestamp": datetime.now().isoformat()
        }

        try:
            with open(self._config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save addon config: {e}")

    def _load_config(self) -> None:
        """Carga configuración y activa addons que estaban activos"""
        if not self._config_file.exists():
            return

        try:
            with open(self._config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)

            for addon_name in config.get("active_addons", []):
                if addon_name in self._addons:
                    self.activate(addon_name)

        except Exception as e:
            logger.error(f"Failed to load addon config: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registry"""
        return {
            "total_addons": len(self._addons),
            "active_addons": len(self.get_active_addons()),
            "inactive_addons": len(self._addons) - len(self.get_active_addons()),
            "addons_dir": str(self._addons_dir),
            "config_file": str(self._config_file)
        }

    def reset(self) -> None:
        """Resetea el registry (útil para testing)"""
        for addon in list(self._addons.values()):
            if addon.active:
                addon.deactivate()
        self._addons.clear()