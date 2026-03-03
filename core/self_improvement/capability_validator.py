# devmind-core/core/self_improvement/capability_validator.py
"""
CapabilityValidator - Valida nuevas capacidades antes de activar.

Este agente asegura que las herramientas y agentes creados
cumplan con estándares de calidad, seguridad y compatibilidad.
"""

import ast
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from ..agents.registry import AgentRegistry
from ..security.permissions import PermissionSystem
from ..security.validator import CodeValidator
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ValidationLevel:
    """Niveles de validación configurables"""
    BASIC = "basic"  # Validaciones mínimas de sintaxis
    STANDARD = "standard"  # Validaciones normales de seguridad
    STRICT = "strict"  # Validaciones completas incluyendo tests


class CapabilityValidator:
    """
    Validador de capacidades del sistema.

    Valida:
    - Herramientas nuevas (código, estructura, seguridad)
    - Agentes nuevos (configuración, permisos, herramientas)
    - Actualizaciones de capacidades existentes
    - Cambios de configuración críticos
    """

    def __init__(self, validation_level: str = ValidationLevel.STANDARD):
        self.validation_level = validation_level
        self.code_validator = CodeValidator(language="python")
        self.tool_registry = ToolRegistry()
        self.agent_registry = AgentRegistry()
        self.permission_system = PermissionSystem()

        self.validations_performed = 0
        self.validations_passed = 0
        self.validations_failed = 0

    def validate_tool(
            self,
            tool_code: str,
            tool_name: str,
            context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Valida una herramienta nueva.

        Args:
            tool_code: Código de la herramienta
            tool_name: Nombre de la herramienta
            context: Contexto adicional

        Returns:
            Dict con resultado de validación
        """
        self.validations_performed += 1

        results = {
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "validation_level": self.validation_level,
            "checks": {}
        }

        # Check 1: Validación de seguridad del código
        code_result = self.code_validator.validate(tool_code)
        results["checks"]["code_security"] = {
            "passed": code_result.valid,
            "findings": [f.to_dict() for f in code_result.findings],
            "has_blocking": code_result.has_blocking,
            "severity_summary": self._summarize_severities(code_result.findings)
        }

        # Check 2: Validación de estructura
        structure_result = self._validate_tool_structure(tool_code, tool_name)
        results["checks"]["structure"] = structure_result

        # Check 3: Validación de documentación
        docs_result = self._validate_documentation(tool_code)
        results["checks"]["documentation"] = docs_result

        # Check 4: Validación de imports
        imports_result = self._validate_imports(tool_code)
        results["checks"]["imports"] = imports_result

        # Check 5: Validación de tests (solo en nivel strict)
        if self.validation_level == ValidationLevel.STRICT:
            tests_result = self._validate_tests(tool_code)
            results["checks"]["tests"] = tests_result

        # Determinar si pasó todas las validaciones críticas
        critical_checks = ["code_security", "structure", "imports"]
        passed = all(
            results["checks"][check].get("passed", False)
            for check in critical_checks
        )

        # En nivel strict, también requerir tests y docs
        if self.validation_level == ValidationLevel.STRICT:
            passed = passed and results["checks"].get("tests", {}).get("passed", False)
            passed = passed and results["checks"].get("documentation", {}).get("passed", False)

        if passed:
            self.validations_passed += 1
        else:
            self.validations_failed += 1

        results["passed"] = passed
        results["summary"] = self._generate_summary(results)

        return results

    def validate_agent(
            self,
            agent_config: Dict[str, Any],
            context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Valida un nuevo agente.

        Args:
            agent_config: Configuración del agente
            context: Contexto adicional

        Returns:
            Dict con resultado de validación
        """
        self.validations_performed += 1

        results = {
            "agent_name": agent_config.get("name", "Unknown"),
            "timestamp": datetime.now().isoformat(),
            "validation_level": self.validation_level,
            "checks": {}
        }

        # Check 1: Configuración requerida
        config_result = self._validate_agent_config(agent_config)
        results["checks"]["configuration"] = config_result

        # Check 2: Nivel de permisos apropiado
        permissions_result = self._validate_permissions(agent_config)
        results["checks"]["permissions"] = permissions_result

        # Check 3: Herramientas asignadas existen
        if "tools" in agent_config:
            tools_result = self._validate_agent_tools(agent_config["tools"])
            results["checks"]["tools"] = tools_result

        # Check 4: Compatibilidad con equipo existente
        compatibility_result = self._validate_compatibility(agent_config)
        results["checks"]["compatibility"] = compatibility_result

        # Determinar si pasó
        passed = all(check.get("passed", False) for check in results["checks"].values())

        if passed:
            self.validations_passed += 1
        else:
            self.validations_failed += 1

        results["passed"] = passed
        results["summary"] = self._generate_summary(results)

        return results

    def _validate_tool_structure(
            self,
            code: str,
            tool_name: str
    ) -> Dict[str, Any]:
        """Valida la estructura básica de una herramienta"""
        errors = []
        warnings = []

        # Verificaciones básicas de string
        if "BaseTool" not in code:
            errors.append("La herramienta debe heredar de core.tools.base.BaseTool")

        if "def execute" not in code:
            errors.append("La herramienta debe implementar método execute(self, **kwargs)")

        if "ToolDefinition" not in code and "definition" not in code:
            errors.append("La herramienta debe tener propiedad definition que retorne ToolDefinition")

        # Validar con AST para mayor precisión
        try:
            tree = ast.parse(code)
            has_correct_inheritance = False
            has_execute_method = False
            has_kwargs = False

            for node in ast.walk(tree):
                # Verificar herencia de clase
                if isinstance(node, ast.ClassDef):
                    for base in node.bases:
                        if isinstance(base, ast.Name) and base.id == "BaseTool":
                            has_correct_inheritance = True
                        elif isinstance(base, ast.Attribute) and base.attr == "BaseTool":
                            has_correct_inheritance = True

                # Verificar método execute
                if isinstance(node, ast.FunctionDef) and node.name == "execute":
                    has_execute_method = True

                    # ✅ CORREGIDO: Verificar **kwargs correctamente
                    # kwarg es un objeto arg individual, no una lista
                    if node.args.kwarg is not None:
                        has_kwargs = node.args.kwarg.arg == "kwargs"

                    # También verificar kwonlyargs
                    if not has_kwargs:
                        has_kwargs = any(
                            isinstance(arg, ast.arg) and arg.arg == "kwargs"
                            for arg in node.args.kwonlyargs
                        )

            # Reportar errores de AST
            if not has_correct_inheritance and "BaseTool" not in code:
                errors.append("No se encontró herencia de BaseTool en el AST")

            if not has_execute_method:
                errors.append("No se encontró método execute() en el AST")

            if has_execute_method and not has_kwargs:
                warnings.append("execute() debería aceptar **kwargs para flexibilidad")

        except SyntaxError as e:
            errors.append(f"Error de sintaxis en el código: {e.msg} (línea {e.lineno})")

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _validate_documentation(self, code: str) -> Dict[str, Any]:
        """Valida que el código tenga documentación adecuada"""
        issues = []

        # Verificar docstring de clase
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    docstring = ast.get_docstring(node)
                    if not docstring:
                        issues.append(f"Clase {node.name} no tiene docstring")
                    elif len(docstring) < 20:
                        issues.append(f"Docstring de {node.name} es muy corto")

                    # Verificar docstrings de métodos
                    for item in node.body:
                        if isinstance(item, ast.FunctionDef) and item.name != "__init__":
                            method_doc = ast.get_docstring(item)
                            if not method_doc and item.name != "execute":
                                issues.append(f"Método {item.name} no tiene docstring")
        except SyntaxError:
            issues.append("No se pudo parsear el código para verificar documentación")

        # Verificar type hints
        has_type_hints = "->" in code and any(
            hint in code for hint in [": str", ": int", ": bool", ": List", ": Dict", ": Optional"]
        )

        if not has_type_hints:
            issues.append("Faltan type hints en los métodos")

        return {
            "passed": len(issues) <= 1,  # Permitir 1 warning menor
            "issues": issues,
            "has_class_docstring": '"""' in code or "'''" in code,
            "has_type_hints": has_type_hints
        }

    def _validate_imports(self, code: str) -> Dict[str, Any]:
        """Valida los imports del código"""
        errors = []
        warnings = []

        # Imports peligrosos
        dangerous_imports = [
            "import os",
            "import sys",
            "import subprocess",
            "import socket",
            "from os import",
            "from sys import",
            "eval(",
            "exec(",
            "__import__(",
            "compile("
        ]

        for dangerous in dangerous_imports:
            if dangerous in code:
                # Permitir si está en comentario o string
                lines = code.split('\n')
                for line in lines:
                    if dangerous in line and not line.strip().startswith('#'):
                        # Verificar si es parte de un string
                        if '"' not in line and "'" not in line:
                            warnings.append(f"Import potencialmente peligroso: {dangerous}")
                        break

        # Imports requeridos para herramientas
        required = [
            "from core.tools.base import",
            "BaseTool",
            "ToolResult"
        ]

        for req in required:
            if req not in code:
                # Verificar import alternativo
                if "core.tools" not in code and "BaseTool" not in code:
                    errors.append(f"Import requerido faltante: {req}")

        return {
            "passed": len(errors) == 0,
            "errors": errors,
            "warnings": warnings
        }

    def _validate_tests(self, code: str) -> Dict[str, Any]:
        """Valida que haya tests incluidos"""
        has_tests = any(pattern in code.lower() for pattern in [
            "test_",
            "unittest",
            "pytest",
            "assert",
            "__main__"
        ])

        if not has_tests:
            return {
                "passed": False,
                "message": "No se encontraron tests unitarios. Se recomienda incluir tests."
            }

        return {
            "passed": True,
            "message": "Tests detectados"
        }

    def _validate_agent_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida configuración de agente"""
        errors = []

        # Campos requeridos
        required_fields = ["name", "role", "goal"]
        for field in required_fields:
            value = config.get(field)
            if not value or (isinstance(value, str) and not value.strip()):
                errors.append(f"Campo requerido faltante o vacío: {field}")

        # Validar nivel
        level_value = config.get("level")
        if hasattr(level_value, 'value'):
            level_value = level_value.value
        elif hasattr(level_value, 'name'):
            level_value = level_value.name

        valid_levels = ["STRATEGIC", "SPECIALIST", "EXECUTION", 1, 2, 3]
        if level_value not in valid_levels:
            errors.append(f"Nivel inválido: {config.get('level')}")

        # Validar temperatura
        temp = config.get("temperature")
        if temp is not None and isinstance(temp, (int, float)):
            if not (0.0 <= temp <= 1.0):
                errors.append("Temperatura debe estar entre 0.0 y 1.0")

        # Validar que el nombre sea único
        try:
            existing = self.agent_registry.get_agent_by_role(config.get("name", ""))
            if existing:
                errors.append(f"Ya existe un agente con nombre/rol: {config['name']}")
        except:
            pass  # Ignorar si registry no disponible

        return {
            "passed": len(errors) == 0,
            "errors": errors
        }

    def _validate_permissions(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida permisos del agente"""
        # En una implementación completa, verificaría contra PermissionSystem
        # Por ahora, validación básica
        return {
            "passed": True,
            "message": "Permisos validados (implementación completa pendiente)"
        }

    def _validate_agent_tools(self, tools: List[str]) -> Dict[str, Any]:
        """Valida herramientas asignadas al agente"""
        invalid_tools = []

        for tool_name in tools:
            tool = self.tool_registry.get(tool_name)
            if not tool:
                invalid_tools.append(tool_name)

        return {
            "passed": len(invalid_tools) == 0,
            "invalid_tools": invalid_tools,
            "message": f"{len(tools) - len(invalid_tools)}/{len(tools)} herramientas válidas" if tools else "Sin herramientas asignadas"
        }

    def _validate_compatibility(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida compatibilidad con el equipo existente"""
        # Verificar conflictos de rol
        existing_roles = [a.role.lower() for a in self.agent_registry._agents.values()]
        if config.get("role", "").lower() in existing_roles:
            return {
                "passed": False,
                "message": f"Ya existe un agente con rol: {config.get('role')}"
            }

        return {
            "passed": True,
            "message": "Compatible con equipo actual"
        }

    def _summarize_severities(self, findings: List) -> Dict[str, int]:
        """Resume hallazgos por severidad"""
        summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "INFO": 0}
        for f in findings:
            sev = getattr(f, 'severity', None)
            if sev and hasattr(sev, 'name'):
                summary[sev.name] = summary.get(sev.name, 0) + 1
        return summary

    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Genera resumen legible de la validación"""
        name = results.get("tool_name") or results.get("agent_name", "Capability")

        if results["passed"]:
            return f"✅ {name} pasó todas las validaciones ({self.validation_level})"
        else:
            failed_checks = [
                k for k, v in results["checks"].items()
                if not v.get("passed", True)
            ]
            return f"❌ Validación falló en: {', '.join(failed_checks)}"

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del validador"""
        return {
            "validations_performed": self.validations_performed,
            "validations_passed": self.validations_passed,
            "validations_failed": self.validations_failed,
            "pass_rate": round(
                self.validations_passed / max(1, self.validations_performed) * 100, 1
            ),
            "validation_level": self.validation_level
        }
