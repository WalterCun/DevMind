# devmind-core/core/config/manager.py
"""
Gestor de configuración de DevMind Core.

Maneja la carga, guarda y actualización de la configuración del agente
desde el sistema de archivos local.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from .schema import AgentConfig


class ConfigManager:
    """
    Gestiona el ciclo de vida de la configuración del agente.

    Singleton que asegura que solo haya una instancia de configuración
    activa en memoria, sincronizada con el sistema de archivos.
    """

    _instance: Optional['ConfigManager'] = None
    _config: Optional[AgentConfig] = None

    # Rutas de configuración
    CONFIG_DIR: Path = Path.home() / ".devmind"
    CONFIG_FILE: Path = CONFIG_DIR / "config.json"
    PROFILES_DIR: Path = CONFIG_DIR / "profiles"

    def __new__(cls) -> 'ConfigManager':
        """Implementa patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self) -> None:
        """Carga la configuración desde el archivo"""
        if self.CONFIG_FILE.exists():
            try:
                with open(self.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self._config = AgentConfig(**data)
            except (json.JSONDecodeError, Exception) as e:
                print(f"⚠️ Error cargando configuración: {e}")
                self._config = None
        else:
            self._config = None

    def get_config(self) -> Optional[AgentConfig]:
        """Obtiene la configuración actual"""
        return self._config

    def is_initialized(self) -> bool:
        """Verifica si el wizard fue completado"""
        return self._config is not None and self._config.initialized

    def requires_init(self) -> bool:
        """Verifica si necesita ejecutar el wizard"""
        return not self.is_initialized()

    def update_config(self, **kwargs) -> AgentConfig:
        """
        Actualiza configuración parcialmente.

        Args:
            **kwargs: Pares clave-valor a actualizar

        Returns:
            AgentConfig: Configuración actualizada

        Raises:
            ValueError: Si la configuración no está inicializada
        """
        if not self._config:
            raise ValueError("Configuración no inicializada. Ejecuta 'devmind init' primero.")

        for key, value in kwargs.items():
            if hasattr(self._config, key):
                setattr(self._config, key, value)

        self._config.updated_at = datetime.now()
        self._save_config()

        return self._config

    def _save_config(self) -> None:
        """Guarda la configuración en el archivo"""
        if not self._config:
            return

        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Usar exclude para evitar campos computados
        config_dict = self._config.model_dump(
            exclude={'created_at', 'updated_at'},
            by_alias=True,
            mode='json'
        )

        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)

    def reset_config(self) -> None:
        """Resetea configuración a valores por defecto"""
        if self.CONFIG_FILE.exists():
            # Crear backup
            backup_path = self.CONFIG_FILE.with_suffix('.json.bak')
            self.CONFIG_FILE.rename(backup_path)
            print(f"📦 Configuración anterior respaldada en: {backup_path}")

        self._config = None

    def get_project_config(self, project_id: str) -> Dict[str, Any]:
        """
        Obtiene configuración específica para un proyecto.

        Args:
            project_id: ID del proyecto

        Returns:
            Dict: Configuración combinada (global + proyecto)
        """
        project_config_path = self.CONFIG_DIR / "projects" / f"{project_id}.json"

        base_config = self._config.dict() if self._config else {}

        if project_config_path.exists():
            with open(project_config_path, 'r', encoding='utf-8') as f:
                project_config = json.load(f)
                base_config.update(project_config)

        return base_config

    def save_project_config(self, project_id: str, config: Dict[str, Any]) -> None:
        """
        Guarda configuración específica para un proyecto.

        Args:
            project_id: ID del proyecto
            config: Configuración del proyecto
        """
        projects_dir = self.CONFIG_DIR / "projects"
        projects_dir.mkdir(parents=True, exist_ok=True)

        project_config_path = projects_dir / f"{project_id}.json"

        with open(project_config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, default=str)

    def get_available_profiles(self) -> list:
        """Obtiene lista de perfiles disponibles"""
        if not self.PROFILES_DIR.exists():
            return []

        profiles = []
        for profile_file in self.PROFILES_DIR.glob("*.json"):
            profiles.append({
                'name': profile_file.stem,
                'path': str(profile_file)
            })

        return profiles

    def load_profile(self, profile_name: str) -> Optional[AgentConfig]:
        """
        Carga un perfil predefinido.

        Args:
            profile_name: Nombre del perfil

        Returns:
            AgentConfig: Configuración del perfil o None
        """
        profile_path = self.PROFILES_DIR / f"{profile_name}.json"

        if not profile_path.exists():
            return None

        with open(profile_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return AgentConfig(**data)

    def save_as_profile(self, profile_name: str) -> bool:
        """
        Guarda la configuración actual como perfil.

        Args:
            profile_name: Nombre del perfil

        Returns:
            bool: True si se guardó exitosamente
        """
        if not self._config:
            return False

        self.PROFILES_DIR.mkdir(parents=True, exist_ok=True)
        profile_path = self.PROFILES_DIR / f"{profile_name}.json"

        config_dict = self._config.model_dump(
            exclude={'created_at', 'updated_at', 'initialized'},
            by_alias=True,
            mode='json'
        )

        with open(profile_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)

        return True

    def get_security_settings(self) -> Dict[str, Any]:
        """Obtiene configuración de seguridad"""
        if not self._config:
            return {}

        return {
            'autonomy_mode': self._config.autonomy_mode,
            'sandbox_enabled': self._config.sandbox_enabled,
            'max_file_write_without_confirm': self._config.max_file_write_without_confirm,
            'allow_internet': self._config.allow_internet,
            'allow_email': self._config.allow_email,
            'allow_self_improvement': self._config.allow_self_improvement,
            'max_concurrent_agents': self._config.max_concurrent_agents,
        }

    def get_agent_identity(self) -> Dict[str, Any]:
        """Obtiene identidad del agente"""
        if not self._config:
            return {}

        return {
            'name': self._config.agent_name,
            'personality': self._config.personality,
            'communication_style': self._config.communication_style,
            'system_prompt': self._config.get_system_prompt(),
        }

    def __repr__(self) -> str:
        if self._config:
            return f"ConfigManager(agent={self._config.agent_name}, initialized={self._config.initialized})"
        return "ConfigManager(not initialized)"