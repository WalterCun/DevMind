# devmind-core/core/security/permissions.py
"""
Sistema de permisos granular para DevMind Core.

Define niveles de autonomía y reglas de seguridad
para controlar qué acciones puede realizar el agente.
"""

import fnmatch
import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable, Set

logger = logging.getLogger(__name__)


class PermissionLevel(Enum):
    """
    Niveles de permiso para acciones del agente.

    L0: Solo lectura - Nunca modifica nada
    L1: Supervisado - Pide confirmación para escribir/ejecutar
    L2: Semi-autónomo - Ejecuta tareas simples sin confirmar
    L3: Autónomo - Ejecuta libremente dentro del sandbox
    """
    L0_READ_ONLY = auto()
    L1_SUPERVISED = auto()
    L2_SEMI_AUTONOMOUS = auto()
    L3_FULL_AUTONOMOUS = auto()

    @property
    def name_label(self) -> str:
        """Etiqueta legible del nivel"""
        labels = {
            PermissionLevel.L0_READ_ONLY: "🔒 Solo Lectura",
            PermissionLevel.L1_SUPERVISED: "🟡 Supervisado",
            PermissionLevel.L2_SEMI_AUTONOMOUS: "🟢 Semi-Autónomo",
            PermissionLevel.L3_FULL_AUTONOMOUS: "🚀 Autónomo"
        }
        return labels.get(self, str(self))


class ActionType(Enum):
    """Tipos de acciones que pueden ser controladas por permisos"""
    # Archivos
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    LIST_DIRECTORY = "list_directory"
    CREATE_DIRECTORY = "create_directory"

    # Código
    EXECUTE_CODE = "execute_code"
    EXECUTE_COMMAND = "execute_command"
    INSTALL_PACKAGE = "install_package"
    IMPORT_MODULE = "import_module"

    # Red
    NETWORK_REQUEST = "network_request"
    DATABASE_QUERY = "database_query"
    API_CALL = "api_call"

    # Sistema
    READ_ENV_VAR = "read_env_var"
    WRITE_ENV_VAR = "write_env_var"
    ACCESS_SECRETS = "access_secrets"

    # Agentes
    CREATE_AGENT = "create_agent"
    MODIFY_AGENT = "modify_agent"
    DELETE_AGENT = "delete_agent"


@dataclass
class SecurityRule:
    """
    Regla de seguridad que define permisos para una acción.
    """
    action: ActionType
    allowed_levels: List[PermissionLevel]
    requires_confirmation: bool = True
    allowed_paths: Optional[List[str]] = None  # Patrones de rutas permitidas
    blocked_paths: Optional[List[str]] = None  # Patrones de rutas bloqueadas
    blocked_patterns: Optional[List[str]] = None  # Patrones de contenido bloqueado
    max_file_size: Optional[int] = None  # Tamaño máximo en bytes
    allowed_extensions: Optional[List[str]] = None  # Extensiones permitidas
    blocked_extensions: Optional[List[str]] = None  # Extensiones bloqueadas
    custom_validator: Optional[Callable[[str, Dict], bool]] = None  # Validador personalizado
    description: str = ""

    def matches_path(self, file_path: str) -> bool:
        """Verifica si una ruta cumple con las restricciones de path"""
        # Verificar rutas permitidas
        if self.allowed_paths:
            if not any(fnmatch.fnmatch(file_path, pattern) for pattern in self.allowed_paths):
                return False

        # Verificar rutas bloqueadas
        if self.blocked_paths:
            if any(fnmatch.fnmatch(file_path, pattern) for pattern in self.blocked_paths):
                return False

        return True

    def matches_content(self, content: str) -> bool:
        """Verifica si el contenido cumple con las restricciones"""
        # Verificar patrones bloqueados en contenido
        if self.blocked_patterns:
            for pattern in self.blocked_patterns:
                if re.search(pattern, content, re.IGNORECASE | re.MULTILINE):
                    return False

        return True

    def matches_extension(self, file_path: str) -> bool:
        """Verifica si la extensión del archivo está permitida"""
        ext = Path(file_path).suffix.lower()

        if self.allowed_extensions and ext not in self.allowed_extensions:
            return False

        if self.blocked_extensions and ext in self.blocked_extensions:
            return False

        return True

    def validate_custom(self, content: str, metadata: Dict) -> bool:
        """Ejecuta validador personalizado si existe"""
        if self.custom_validator:
            try:
                return self.custom_validator(content, metadata)
            except Exception as e:
                logger.error(f"Custom validator error: {e}")
                return False
        return True


class PermissionSystem:
    """
    Sistema central de gestión de permisos.

    Evalúa si una acción está permitida según:
    - Nivel de autonomía configurado
    - Reglas de seguridad definidas
    - Contexto de la acción (ruta, contenido, metadata)
    """

    # Reglas por defecto para cada tipo de acción
    DEFAULT_RULES: Dict[ActionType, SecurityRule] = {
        # Archivos - Lectura (permitido en todos los niveles)
        ActionType.READ_FILE: SecurityRule(
            action=ActionType.READ_FILE,
            allowed_levels=list(PermissionLevel),
            requires_confirmation=False,
            blocked_paths=["/etc/*", "/proc/*", "/sys/*", "C:\\Windows\\*"],
            description="Lectura de archivos"
        ),

        # Archivos - Escritura (requiere al menos L1)
        ActionType.WRITE_FILE: SecurityRule(
            action=ActionType.WRITE_FILE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS,
                            PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=True,
            allowed_paths=["projects/*", "src/*", "app/*", "*.py", "*.js", "*.ts"],
            blocked_paths=["/*", "*/.env*", "*/secrets/*", "*/credentials/*"],
            blocked_extensions=[".exe", ".bat", ".sh", ".cmd", ".ps1"],
            max_file_size=10 * 1024 * 1024,  # 10MB
            description="Escritura de archivos de código"
        ),

        # Archivos - Eliminación (alto riesgo)
        ActionType.DELETE_FILE: SecurityRule(
            action=ActionType.DELETE_FILE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS],
            requires_confirmation=True,
            blocked_paths=["*", ".*", "projects/*", "*/node_modules/*", "*/venv/*"],
            description="Eliminación de archivos (muy restringida)"
        ),

        # Directorios
        ActionType.LIST_DIRECTORY: SecurityRule(
            action=ActionType.LIST_DIRECTORY,
            allowed_levels=list(PermissionLevel),
            requires_confirmation=False,
            blocked_paths=["/proc/*", "/sys/*"],
            description="Listado de directorios"
        ),

        ActionType.CREATE_DIRECTORY: SecurityRule(
            action=ActionType.CREATE_DIRECTORY,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS,
                            PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=False,
            allowed_paths=["projects/*", "src/*", "app/*"],
            description="Creación de directorios"
        ),

        # Ejecución de código
        ActionType.EXECUTE_CODE: SecurityRule(
            action=ActionType.EXECUTE_CODE,
            allowed_levels=[PermissionLevel.L2_SEMI_AUTONOMOUS, PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=False,
            blocked_patterns=[
                r'os\.system\s*\(',
                r'subprocess\.(call|run|Popen)\s*\([^)]*shell\s*=\s*True',
                r'__import__\s*\(\s*["\']os["\']',
                r'eval\s*\(',
                r'exec\s*\(',
            ],
            description="Ejecución de código Python"
        ),

        ActionType.EXECUTE_COMMAND: SecurityRule(
            action=ActionType.EXECUTE_COMMAND,
            allowed_levels=[PermissionLevel.L2_SEMI_AUTONOMOUS, PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=True,
            blocked_patterns=[
                r'rm\s+-rf\s+/',
                r'del\s+/[qs]',
                r'format\s+[cdefg]:',
                r'mkfs',
                r'dd\s+if=',
            ],
            description="Ejecución de comandos de shell"
        ),

        # Paquetes
        ActionType.INSTALL_PACKAGE: SecurityRule(
            action=ActionType.INSTALL_PACKAGE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS],
            requires_confirmation=True,
            allowed_extensions=[".whl", ".tar.gz"],
            description="Instalación de paquetes"
        ),

        # Red
        ActionType.NETWORK_REQUEST: SecurityRule(
            action=ActionType.NETWORK_REQUEST,
            allowed_levels=[PermissionLevel.L2_SEMI_AUTONOMOUS, PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=True,
            description="Solicitudes de red HTTP/HTTPS"
        ),

        # Base de datos
        ActionType.DATABASE_QUERY: SecurityRule(
            action=ActionType.DATABASE_QUERY,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS,
                            PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=False,
            blocked_patterns=[
                r'DROP\s+(TABLE|DATABASE|SCHEMA)',
                r'TRUNCATE\s+TABLE',
                r'DELETE\s+FROM\s+\w+\s*;',  # DELETE sin WHERE
            ],
            description="Consultas a base de datos"
        ),

        # Variables de entorno
        ActionType.READ_ENV_VAR: SecurityRule(
            action=ActionType.READ_ENV_VAR,
            allowed_levels=[PermissionLevel.L1_SUPERVISED, PermissionLevel.L2_SEMI_AUTONOMOUS,
                            PermissionLevel.L3_FULL_AUTONOMOUS],
            requires_confirmation=False,
            blocked_patterns=[r'(?i)(password|secret|key|token|credential)'],
            description="Lectura de variables de entorno"
        ),

        ActionType.ACCESS_SECRETS: SecurityRule(
            action=ActionType.ACCESS_SECRETS,
            allowed_levels=[],  # Nunca permitido automáticamente
            requires_confirmation=True,
            description="Acceso a secretos/credenciales (siempre requiere confirmación explícita)"
        ),
    }

    def __init__(
            self,
            autonomy_level: PermissionLevel = PermissionLevel.L1_SUPERVISED,
            project_root: Optional[str] = None,
            custom_rules: Optional[List[SecurityRule]] = None
    ):
        self.autonomy_level = autonomy_level
        self.project_root = Path(project_root).resolve() if project_root else None
        self.rules: Dict[ActionType, SecurityRule] = self.DEFAULT_RULES.copy()

        # Agregar reglas personalizadas
        if custom_rules:
            for rule in custom_rules:
                self.rules[rule.action] = rule

        # Lista de acciones que requieren confirmación explícita siempre
        self.always_confirm: Set[ActionType] = {
            ActionType.DELETE_FILE,
            ActionType.ACCESS_SECRETS,
            ActionType.EXECUTE_COMMAND,
        }

    def check_permission(
            self,
            action: ActionType,
            file_path: Optional[str] = None,
            content: Optional[str] = None,
            metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Verifica si una acción está permitida.

        Returns:
            Dict con:
            - allowed: bool
            - requires_confirmation: bool
            - reason: str (si está denegado)
            - rule: SecurityRule (la regla aplicada)
        """
        metadata = metadata or {}
        rule = self.rules.get(action)

        if not rule:
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"No rule defined for action: {action.value}",
                "rule": None
            }

        # Verificar nivel de autonomía
        if self.autonomy_level not in rule.allowed_levels:
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"Action {action.value} requires level >= {min(rule.allowed_levels, key=lambda x: x.value).name}",
                "rule": rule
            }

        # Verificar restricciones de path
        if file_path and not rule.matches_path(file_path):
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"Path '{file_path}' is not allowed for action {action.value}",
                "rule": rule
            }

        # Verificar restricciones de extensión
        if file_path and not rule.matches_extension(file_path):
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"File extension not allowed for action {action.value}",
                "rule": rule
            }

        # Verificar restricciones de contenido
        if content and not rule.matches_content(content):
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"Content contains blocked patterns for action {action.value}",
                "rule": rule
            }

        # Verificar tamaño de archivo
        if content and rule.max_file_size and len(content.encode('utf-8')) > rule.max_file_size:
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"Content exceeds max size of {rule.max_file_size} bytes",
                "rule": rule
            }

        # Ejecutar validador personalizado
        if content and not rule.validate_custom(content, metadata):
            return {
                "allowed": False,
                "requires_confirmation": False,
                "reason": f"Custom validation failed for action {action.value}",
                "rule": rule
            }

        # Determinar si requiere confirmación
        requires_confirmation = (
                rule.requires_confirmation or
                action in self.always_confirm or
                self.autonomy_level == PermissionLevel.L1_SUPERVISED
        )

        # En modo autónomo, algunas acciones no requieren confirmación
        if self.autonomy_level == PermissionLevel.L3_FULL_AUTONOMOUS:
            requires_confirmation = action in self.always_confirm

        return {
            "allowed": True,
            "requires_confirmation": requires_confirmation,
            "reason": "Permission granted",
            "rule": rule
        }

    def add_rule(self, rule: SecurityRule) -> None:
        """Agrega o actualiza una regla de seguridad"""
        self.rules[rule.action] = rule
        logger.info(f"Added security rule for {rule.action.value}")

    def remove_rule(self, action: ActionType) -> bool:
        """Elimina una regla de seguridad"""
        if action in self.rules and action not in self.DEFAULT_RULES:
            del self.rules[action]
            logger.info(f"Removed custom rule for {action.value}")
            return True
        return False

    def get_effective_level(self, action: ActionType) -> Optional[PermissionLevel]:
        """Obtiene el nivel mínimo requerido para una acción"""
        rule = self.rules.get(action)
        if rule and rule.allowed_levels:
            return min(rule.allowed_levels, key=lambda x: x.value)
        return None

    def list_allowed_actions(self) -> List[ActionType]:
        """Lista acciones permitidas para el nivel actual"""
        return [
            action for action, rule in self.rules.items()
            if self.autonomy_level in rule.allowed_levels
        ]

    def get_security_summary(self) -> Dict[str, Any]:
        """Genera resumen de configuración de seguridad"""
        return {
            "autonomy_level": self.autonomy_level.name,
            "autonomy_label": self.autonomy_level.name_label,
            "project_root": str(self.project_root) if self.project_root else None,
            "total_rules": len(self.rules),
            "allowed_actions": [a.value for a in self.list_allowed_actions()],
            "always_confirm": [a.value for a in self.always_confirm],
        }