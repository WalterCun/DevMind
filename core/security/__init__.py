# devmind-core/core/security/__init__.py
"""
Módulo de seguridad de DevMind Core.

Proporciona sandboxing, permisos, validación y auditoría
para ejecución segura de código generado por IA.
"""

from .permissions import PermissionLevel, ActionType, SecurityRule, PermissionSystem
from .sandbox import ExecutionSandbox, SandboxConfig, SandboxResult
from .validator import CodeValidator, ValidationResult, Severity, ValidationFinding
from .auditor import SecurityAuditor, AuditEntry, AuditLevel, AuditCategory, AuditStatus
from .rules import RuleEngine, SecurityRule as RuleSecurity, RuleAction, RuleCondition, RuleOperator

__all__ = [
    # Permissions
    "PermissionLevel",
    "ActionType",
    "SecurityRule",
    "PermissionSystem",
    # Sandbox
    "ExecutionSandbox",
    "SandboxConfig",
    "SandboxResult",
    # Validator
    "CodeValidator",
    "ValidationResult",
    "Severity",
    "ValidationFinding",
    # Auditor
    "SecurityAuditor",
    "AuditEntry",
    "AuditLevel",
    "AuditCategory",
    "AuditStatus",
    # Rules
    "RuleEngine",
    "RuleSecurity",
    "RuleAction",
    "RuleCondition",
    "RuleOperator",
]