from enum import Enum
from typing import List, Dict, Any, Callable
from dataclasses import dataclass


class PermissionLevel(Enum):
    L0_READ_ONLY = 0  # Solo lectura
    L1_SUPERVISED_WRITE = 1  # Escritura con confirmación
    L2_LIMITED_AUTONOMY = 2  # Autonomía limitada
    L3_FULL_AUTONOMY = 3  # Autonomía total (sandbox)


class ActionType(Enum):
    READ_FILE = "read_file"
    WRITE_FILE = "write_file"
    DELETE_FILE = "delete_file"
    EXECUTE_CODE = "execute_code"
    INSTALL_PACKAGE = "install_package"
    NETWORK_ACCESS = "network_access"
    DATABASE_ACCESS = "database_access"
    EXTERNAL_API = "external_api"


@dataclass
class SecurityRule:
    action: ActionType
    allowed_levels: List[PermissionLevel]
    requires_confirmation: bool
    max_file_size: int = None
    allowed_paths: List[str] = None
    blocked_patterns: List[str] = None


class PermissionSystem:
    """Sistema de permisos y seguridad"""

    DEFAULT_RULES = [
        SecurityRule(
            action=ActionType.READ_FILE,
            allowed_levels=[PermissionLevel.L0_READ_ONLY, PermissionLevel.L1_SUPERVISED_WRITE,
                            PermissionLevel.L2_LIMITED_AUTONOMY, PermissionLevel.L3_FULL_AUTONOMY],
            requires_confirmation=False
        ),
        SecurityRule(
            action=ActionType.WRITE_FILE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED_WRITE, PermissionLevel.L2_LIMITED_AUTONOMY,
                            PermissionLevel.L3_FULL_AUTONOMY],
            requires_confirmation=True,
            max_file_size=1024 * 1024,  # 1MB
            allowed_paths=["./projects/"],
            blocked_patterns=["*.sh", "*.bat", ".*"]
        ),
        SecurityRule(
            action=ActionType.DELETE_FILE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED_WRITE, PermissionLevel.L2_LIMITED_AUTONOMY],
            requires_confirmation=True,
            blocked_patterns=["*", ".*", "projects/*"]  # Nunca borrar todo
        ),
        SecurityRule(
            action=ActionType.EXECUTE_CODE,
            allowed_levels=[PermissionLevel.L2_LIMITED_AUTONOMY, PermissionLevel.L3_FULL_AUTONOMY],
            requires_confirmation=False
        ),
        SecurityRule(
            action=ActionType.INSTALL_PACKAGE,
            allowed_levels=[PermissionLevel.L1_SUPERVISED_WRITE, PermissionLevel.L2_LIMITED_AUTONOMY],
            requires_confirmation=True
        ),
        SecurityRule(
            action=ActionType.NETWORK_ACCESS,
            allowed_levels=[PermissionLevel.L2_LIMITED_AUTONOMY],
            requires_confirmation=True
        ),
    ]

    def __init__(self, autonomy_mode: str = "supervised"):
        self.autonomy_mode = autonomy_mode
        self.rules = self.DEFAULT_RULES.copy()
        self.permission_level = self._get_permission_level(autonomy_mode)

    def _get_permission_level(self, mode: str) -> PermissionLevel:
        """Mapea modo de autonomía a nivel de permiso"""
        mapping = {
            'supervised': PermissionLevel.L1_SUPERVISED_WRITE,
            'semi_autonomous': PermissionLevel.L2_LIMITED_AUTONOMY,
            'full_autonomous': PermissionLevel.L3_FULL_AUTONOMY
        }
        return mapping.get(mode, PermissionLevel.L1_SUPERVISED_WRITE)

    def check_permission(self, action: ActionType, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Verifica si una acción está permitida"""
        rule = self._find_rule(action)

        if not rule:
            return {'allowed': False, 'reason': 'No rule found'}

        if self.permission_level not in rule.allowed_levels:
            return {
                'allowed': False,
                'reason': f'Permission level {self.permission_level} not allowed for {action}',
                'requires_upgrade': True
            }

        # Verificaciones adicionales
        if context:
            if rule.max_file_size and context.get('file_size', 0) > rule.max_file_size:
                return {'allowed': False, 'reason': 'File size exceeds limit'}

            if rule.blocked_patterns:
                file_path = context.get('file_path', '')
                for pattern in rule.blocked_patterns:
                    if self._matches_pattern(file_path, pattern):
                        return {'allowed': False, 'reason': f'Pattern {pattern} is blocked'}

        return {
            'allowed': True,
            'requires_confirmation': rule.requires_confirmation and self.permission_level < PermissionLevel.L3_FULL_AUTONOMY
        }

    def _find_rule(self, action: ActionType) -> SecurityRule:
        """Encuentra la regla para una acción"""
        for rule in self.rules:
            if rule.action == action:
                return rule
        return None

    def _matches_pattern(self, path: str, pattern: str) -> bool:
        """Verifica si un path coincide con un patrón"""
        import fnmatch
        return fnmatch.fnmatch(path, pattern)

    def add_rule(self, rule: SecurityRule):
        """Agrega una regla personalizada"""
        self.rules.append(rule)

    def get_security_report(self) -> Dict[str, Any]:
        """Genera reporte de seguridad"""
        return {
            'autonomy_mode': self.autonomy_mode,
            'permission_level': self.permission_level.value,
            'total_rules': len(self.rules),
            'rules': [
                {
                    'action': rule.action.value,
                    'allowed_levels': [l.value for l in rule.allowed_levels],
                    'requires_confirmation': rule.requires_confirmation
                }
                for rule in self.rules
            ]
        }