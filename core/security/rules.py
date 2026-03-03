# devmind-core/core/security/rules.py
"""
Motor de reglas de seguridad para DevMind Core.

Permite definir, cargar y ejecutar reglas de seguridad
personalizables para controlar el comportamiento del agente.
"""

import json
import yaml
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable, Union
import re

logger = logging.getLogger(__name__)


class RuleOperator(Enum):
    """Operadores disponibles para reglas"""
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    REGEX_MATCH = "regex_match"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    IN_LIST = "in_list"
    NOT_IN_LIST = "not_in_list"
    EXISTS = "exists"
    NOT_EXISTS = "not_exists"


class RuleAction(Enum):
    """Acciones que puede tomar una regla"""
    ALLOW = "allow"
    BLOCK = "block"
    REQUIRE_CONFIRMATION = "require_confirmation"
    LOG_ONLY = "log_only"
    TRIGGER_ALERT = "trigger_alert"
    MODIFY_CONTEXT = "modify_context"


@dataclass
class RuleCondition:
    """
    Condición individual dentro de una regla.
    """
    field: str
    operator: RuleOperator
    value: Any

    def evaluate(self, context: Dict[str, Any]) -> bool:
        """Evalúa la condición contra un contexto"""
        # Obtener valor del contexto
        field_value = self._get_nested_value(context, self.field)

        if self.operator == RuleOperator.EQUALS:
            return field_value == self.value
        elif self.operator == RuleOperator.NOT_EQUALS:
            return field_value != self.value
        elif self.operator == RuleOperator.CONTAINS:
            return self.value in str(field_value)
        elif self.operator == RuleOperator.NOT_CONTAINS:
            return self.value not in str(field_value)
        elif self.operator == RuleOperator.REGEX_MATCH:
            return bool(re.search(self.value, str(field_value)))
        elif self.operator == RuleOperator.GREATER_THAN:
            return float(field_value) > float(self.value)
        elif self.operator == RuleOperator.LESS_THAN:
            return float(field_value) < float(self.value)
        elif self.operator == RuleOperator.IN_LIST:
            return field_value in self.value
        elif self.operator == RuleOperator.NOT_IN_LIST:
            return field_value not in self.value
        elif self.operator == RuleOperator.EXISTS:
            return field_value is not None
        elif self.operator == RuleOperator.NOT_EXISTS:
            return field_value is None

        return False

    def _get_nested_value(self, obj: Dict, field_path: str) -> Any:
        """Obtiene valor de campo anidado (ej: 'user.permissions.level')"""
        parts = field_path.split('.')
        value = obj

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

            if value is None:
                return None

        return value


@dataclass
class SecurityRule:
    """
    Regla de seguridad completa.
    """
    id: str
    name: str
    description: str
    enabled: bool = True
    priority: int = 100  # Menor número = mayor prioridad
    conditions: List[RuleCondition] = field(default_factory=list)
    action: RuleAction = RuleAction.ALLOW
    action_params: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def evaluate(self, context: Dict[str, Any]) -> Optional[RuleAction]:
        """
        Evalúa la regla contra un contexto.

        Returns:
            RuleAction si la regla coincide, None si no
        """
        if not self.enabled:
            return None

        # Todas las condiciones deben cumplirse (AND)
        if not self.conditions:
            return self.action if self.enabled else None

        all_match = all(cond.evaluate(context) for cond in self.conditions)

        return self.action if all_match else None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "enabled": self.enabled,
            "priority": self.priority,
            "conditions": [
                {"field": c.field, "operator": c.operator.value, "value": c.value}
                for c in self.conditions
            ],
            "action": self.action.value,
            "action_params": self.action_params,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SecurityRule':
        return cls(
            id=data["id"],
            name=data["name"],
            description=data.get("description", ""),
            enabled=data.get("enabled", True),
            priority=data.get("priority", 100),
            conditions=[
                RuleCondition(
                    field=c["field"],
                    operator=RuleOperator(c["operator"]),
                    value=c["value"]
                )
                for c in data.get("conditions", [])
            ],
            action=RuleAction(data.get("action", "allow")),
            action_params=data.get("action_params", {}),
            metadata=data.get("metadata", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if "created_at" in data else datetime.now(),
            updated_at=datetime.fromisoformat(data["updated_at"]) if "updated_at" in data else datetime.now()
        )


class RuleEngine:
    """
    Motor de evaluación de reglas de seguridad.

    Características:
    - Carga de reglas desde archivos (JSON, YAML)
    - Evaluación en orden de prioridad
    - Hot-reload de reglas
    - Validación de sintaxis de reglas
    """

    def __init__(self, rules_dir: Optional[str] = None):
        self.rules: Dict[str, SecurityRule] = {}
        self.rules_dir = Path(rules_dir) if rules_dir else Path.home() / ".devmind" / "rules"
        self._callbacks: Dict[RuleAction, List[Callable]] = {action: [] for action in RuleAction}

        # Cargar reglas por defecto
        self._load_default_rules()

        # Cargar reglas personalizadas
        self._load_custom_rules()

    def _load_default_rules(self) -> None:
        """Carga reglas de seguridad por defecto"""
        default_rules = [
            # Bloquear eliminación de archivos críticos
            SecurityRule(
                id="block_critical_delete",
                name="Bloquear eliminación de archivos críticos",
                description="Previene eliminación de archivos del sistema y configuración",
                priority=10,
                conditions=[
                    RuleCondition("action", RuleOperator.EQUALS, "delete_file"),
                    RuleCondition("file_path", RuleOperator.REGEX_MATCH, r"^(/etc|/proc|/sys|C:\\Windows)"),
                ],
                action=RuleAction.BLOCK,
                action_params={"reason": "Archivo crítico del sistema"}
            ),

            # Requerir confirmación para ejecución de código
            SecurityRule(
                id="confirm_code_execution",
                name="Confirmar ejecución de código",
                description="Requiere confirmación antes de ejecutar código generado",
                priority=20,
                conditions=[
                    RuleCondition("action", RuleOperator.EQUALS, "execute_code"),
                    RuleCondition("risk_score", RuleOperator.GREATER_THAN, 0.5),
                ],
                action=RuleAction.REQUIRE_CONFIRMATION,
                action_params={"timeout_seconds": 300}
            ),

            # Alertar sobre acceso a secretos
            SecurityRule(
                id="alert_secret_access",
                name="Alertar acceso a secretos",
                description="Genera alerta cuando se accede a variables sensibles",
                priority=15,
                conditions=[
                    RuleCondition("action", RuleOperator.EQUALS, "read_env_var"),
                    RuleCondition("variable_name", RuleOperator.REGEX_MATCH, r"(?i)(password|secret|key|token)"),
                ],
                action=RuleAction.TRIGGER_ALERT,
                action_params={"severity": "high"}
            ),

            # Loggear todas las operaciones de red
            SecurityRule(
                id="log_network_activity",
                name="Loggear actividad de red",
                description="Registra todas las solicitudes de red para auditoría",
                priority=50,
                conditions=[
                    RuleCondition("action", RuleOperator.EQUALS, "network_request"),
                ],
                action=RuleAction.LOG_ONLY,
                action_params={"include_response": True}
            ),
        ]

        for rule in default_rules:
            self.rules[rule.id] = rule

        logger.info(f"Loaded {len(default_rules)} default security rules")

    def _load_custom_rules(self) -> None:
        """Carga reglas personalizadas desde archivos"""
        if not self.rules_dir.exists():
            self.rules_dir.mkdir(parents=True, exist_ok=True)
            return

        for file_path in self.rules_dir.glob("*.json"):
            self._load_rules_from_file(file_path)

        for file_path in self.rules_dir.glob("*.yaml"):
            self._load_rules_from_file(file_path)

        for file_path in self.rules_dir.glob("*.yml"):
            self._load_rules_from_file(file_path)

    def _load_rules_from_file(self, file_path: Path) -> None:
        """Carga reglas desde un archivo JSON o YAML"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                else:
                    data = json.load(f)

            # Manejar lista o diccionario de reglas
            rules_list = data if isinstance(data, list) else data.get("rules", [])

            for rule_data in rules_list:
                rule = SecurityRule.from_dict(rule_data)
                self.rules[rule.id] = rule
                logger.debug(f"Loaded rule: {rule.id}")

            logger.info(f"Loaded rules from {file_path}")

        except Exception as e:
            logger.error(f"Failed to load rules from {file_path}: {e}")

    def add_rule(self, rule: SecurityRule) -> bool:
        """Agrega o actualiza una regla"""
        self.rules[rule.id] = rule
        rule.updated_at = datetime.now()
        logger.info(f"Added/updated rule: {rule.id}")
        return True

    def remove_rule(self, rule_id: str) -> bool:
        """Elimina una regla"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            logger.info(f"Removed rule: {rule_id}")
            return True
        return False

    def enable_rule(self, rule_id: str) -> bool:
        """Habilita una regla"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            self.rules[rule_id].updated_at = datetime.now()
            return True
        return False

    def disable_rule(self, rule_id: str) -> bool:
        """Deshabilita una regla"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self.rules[rule_id].updated_at = datetime.now()
            return True
        return False

    def evaluate(
            self,
            context: Dict[str, Any],
            default_action: RuleAction = RuleAction.ALLOW
    ) -> RuleAction:
        """
        Evalúa todas las reglas contra un contexto.

        Las reglas se evalúan en orden de prioridad (menor número primero).
        La primera regla que coincide determina la acción.

        Args:
            context: Contexto de la acción a evaluar
            default_action: Acción por defecto si ninguna regla coincide

        Returns:
            RuleAction a tomar
        """
        # Ordenar reglas por prioridad
        sorted_rules = sorted(
            [r for r in self.rules.values() if r.enabled],
            key=lambda r: r.priority
        )

        # Evaluar cada regla
        for rule in sorted_rules:
            action = rule.evaluate(context)
            if action:
                logger.debug(f"Rule matched: {rule.id} -> {action.value}")
                return action

        return default_action

    def evaluate_with_details(
            self,
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Evalúa reglas y retorna detalles completos.

        Returns:
            Dict con acción, regla coincidente, y todas las evaluaciones
        """
        sorted_rules = sorted(
            [r for r in self.rules.values() if r.enabled],
            key=lambda r: r.priority
        )

        evaluations = []
        matched_rule = None
        final_action = RuleAction.ALLOW

        for rule in sorted_rules:
            action = rule.evaluate(context)
            evaluations.append({
                "rule_id": rule.id,
                "rule_name": rule.name,
                "matched": action is not None,
                "action": action.value if action else None
            })

            if action and matched_rule is None:
                matched_rule = rule
                final_action = action

        return {
            "action": final_action.value,
            "matched_rule": matched_rule.to_dict() if matched_rule else None,
            "all_evaluations": evaluations,
            "rules_evaluated": len(evaluations)
        }

    def register_callback(
            self,
            action: RuleAction,
            callback: Callable[[Dict[str, Any], SecurityRule], None]
    ) -> None:
        """Registra callback para cuando una regla dispara una acción"""
        self._callbacks[action].append(callback)

    def export_rules(self, file_path: str, format: str = "json") -> bool:
        """Exporta todas las reglas a archivo"""
        try:
            output_path = Path(file_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)

            rules_data = [rule.to_dict() for rule in self.rules.values()]

            with open(output_path, 'w', encoding='utf-8') as f:
                if format == "json":
                    json.dump({"rules": rules_data}, f, indent=2, ensure_ascii=False)
                elif format == "yaml":
                    yaml.dump({"rules": rules_data}, f, default_flow_style=False, allow_unicode=True)

            logger.info(f"Exported {len(rules_data)} rules to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export rules: {e}")
            return False

    def import_rules(self, file_path: str, merge: bool = True) -> int:
        """
        Importa reglas desde archivo.

        Args:
            file_path: Ruta del archivo
            merge: Si True, fusiona con reglas existentes; si False, reemplaza

        Returns:
            Número de reglas importadas
        """
        if not merge:
            self.rules.clear()

        self._load_rules_from_file(Path(file_path))
        return len(self.rules)

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del motor de reglas"""
        enabled = sum(1 for r in self.rules.values() if r.enabled)
        disabled = len(self.rules) - enabled

        by_action = {}
        for action in RuleAction:
            by_action[action.value] = sum(
                1 for r in self.rules.values()
                if r.enabled and r.action == action
            )

        return {
            "total_rules": len(self.rules),
            "enabled": enabled,
            "disabled": disabled,
            "by_action": by_action,
            "rules_dir": str(self.rules_dir),
            "callbacks_registered": sum(len(cbs) for cbs in self._callbacks.values())
        }

        # Al final del archivo, asegurarse de que no haya código truncado:

    def list_rules(self, enabled_only: bool = False) -> List[Dict[str, Any]]:
        """Lista todas las reglas"""
        rules = self.rules.values()
        if enabled_only:
            rules = [r for r in rules if r.enabled]

        return [
            {
                "id": r.id,
                "name": r.name,
                "description": r.description,
                "enabled": r.enabled,
                "priority": r.priority,
                "action": r.action.value
            }
            for r in sorted(rules, key=lambda r: r.priority)
        ]