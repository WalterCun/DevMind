# devmind-core/core/security/validator.py
"""
Validador de código para DevMind Core.

Analiza código generado por IA para detectar:
- Patrones peligrosos
- Vulnerabilidades de seguridad
- Código malicioso potencial
- Violaciones de políticas del proyecto
"""

import ast
import hashlib
import logging
import re
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Any, Optional, List, Set, Callable

logger = logging.getLogger(__name__)


class Severity(Enum):
    """Niveles de severidad para hallazgos de validación"""
    INFO = auto()  # Informativo, no requiere acción
    LOW = auto()  # Bajo riesgo, revisar cuando sea posible
    MEDIUM = auto()  # Riesgo medio, debería corregirse
    HIGH = auto()  # Alto riesgo, debe corregirse antes de ejecutar
    CRITICAL = auto()  # Crítico, bloquear ejecución inmediatamente


class ValidationRuleType(Enum):
    """Tipos de reglas de validación"""
    PATTERN = auto()  # Búsqueda de patrones regex
    AST_ANALYSIS = auto()  # Análisis del árbol de sintaxis
    IMPORT_CHECK = auto()  # Verificación de imports
    COMPLEXITY = auto()  # Métricas de complejidad
    CUSTOM = auto()  # Validador personalizado


@dataclass
class ValidationFinding:
    """
    Hallazgo de una validación de código.
    """
    rule_name: str
    severity: Severity
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    rule_type: ValidationRuleType = ValidationRuleType.PATTERN

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_name": self.rule_name,
            "severity": self.severity.name,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet[:100] if self.code_snippet else None,
            "suggestion": self.suggestion,
            "rule_type": self.rule_type.name
        }


@dataclass
class ValidationResult:
    """
    Resultado completo de una validación de código.
    """
    valid: bool
    findings: List[ValidationFinding] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    code_hash: str = ""
    language: str = ""

    @property
    def has_critical(self) -> bool:
        """Verifica si hay hallazgos críticos"""
        return any(f.severity == Severity.CRITICAL for f in self.findings)

    @property
    def has_blocking(self) -> bool:
        """Verifica si hay hallazgos que bloquean la ejecución"""
        return any(f.severity in [Severity.CRITICAL, Severity.HIGH] for f in self.findings)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "valid": self.valid,
            "has_critical": self.has_critical,
            "has_blocking": self.has_blocking,
            "findings_count": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
            "warnings": self.warnings,
            "code_hash": self.code_hash,
            "language": self.language
        }


class CodeValidator:
    """
    Validador principal de código para DevMind Core.

    Ejecuta múltiples reglas de validación para asegurar
    que el código generado sea seguro y cumpla con políticas.
    """

    # Patrones peligrosos por lenguaje
    DANGEROUS_PATTERNS: Dict[str, List[Dict[str, Any]]] = {
        "python": [
            {
                "name": "exec_eval_usage",
                "pattern": r'\b(exec|eval|compile)\s*\(',
                "severity": Severity.HIGH,
                "message": "Uso de exec/eval/compile puede ejecutar código arbitrario",
                "suggestion": "Usar alternativas seguras como ast.literal_eval para datos"
            },
            {
                "name": "os_system_usage",
                "pattern": r'os\.system\s*\(|subprocess\.(call|run|Popen).*shell\s*=\s*True',
                "severity": Severity.HIGH,
                "message": "Ejecución de shell con input potencialmente no sanitizado",
                "suggestion": "Usar subprocess con lista de argumentos y shell=False"
            },
            {
                "name": "pickle_usage",
                "pattern": r'pickle\.(load|loads|Unpickler)',
                "severity": Severity.HIGH,
                "message": "pickle puede ejecutar código arbitrario al deserializar",
                "suggestion": "Usar json, msgpack o formatos seguros para serialización"
            },
            {
                "name": "hardcoded_credentials",
                "pattern": r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
                "severity": Severity.CRITICAL,
                "message": "Credenciales hardcodeadas detectadas",
                "suggestion": "Usar variables de entorno o sistema de secretos"
            },
            {
                "name": "sql_injection_risk",
                "pattern": r'execute\s*\(\s*f?["\'].*\{.*\}.*["\']',
                "severity": Severity.CRITICAL,
                "message": "Posible inyección SQL con string formatting",
                "suggestion": "Usar parámetros parametrizados en queries"
            },
            {
                "name": "infinite_loop_risk",
                "pattern": r'while\s+True\s*:\s*(?!.*\b(break|return)\b)',
                "severity": Severity.MEDIUM,
                "message": "Bucle while True sin break/return visible",
                "suggestion": "Asegurar condición de salida o timeout"
            },
        ],
        "javascript": [
            {
                "name": "eval_usage",
                "pattern": r'\beval\s*\(',
                "severity": Severity.HIGH,
                "message": "Uso de eval() puede ejecutar código arbitrario",
                "suggestion": "Evitar eval, usar alternativas seguras"
            },
            {
                "name": "innerhtml_usage",
                "pattern": r'\.innerHTML\s*=',
                "severity": Severity.MEDIUM,
                "message": "innerHTML puede causar XSS con input no sanitizado",
                "suggestion": "Usar textContent o librerías que saniticen"
            },
            {
                "name": "hardcoded_credentials",
                "pattern": r'(?i)(password|secret|api[_-]?key|token)\s*[:=]\s*["\'][^"\']+["\']',
                "severity": Severity.CRITICAL,
                "message": "Credenciales hardcodeadas detectadas",
                "suggestion": "Usar variables de entorno"
            },
        ],
    }

    # Imports peligrosos por lenguaje
    DANGEROUS_IMPORTS: Dict[str, Set[str]] = {
        "python": {
            "os", "sys", "subprocess", "socket", "http.client",
            "urllib", "requests", "pickle", "marshal", "shelve",
            "ctypes", "ctypes.util", "importlib", "__import__",
        },
        "javascript": {
            "child_process", "fs", "net", "http", "https", "eval",
        },
    }

    def __init__(
            self,
            language: str = "python",
            custom_rules: Optional[List[Dict[str, Any]]] = None,
            allowed_imports: Optional[Set[str]] = None,
            blocked_imports: Optional[Set[str]] = None
    ):
        self.language = language.lower()
        self.custom_rules = custom_rules or []
        self.allowed_imports = allowed_imports or set()
        self.blocked_imports = blocked_imports or set()

        # Compilar patrones para mejor rendimiento
        self._compiled_patterns = []
        for pattern_def in self.DANGEROUS_PATTERNS.get(language, []):
            compiled = {
                **pattern_def,
                "compiled": re.compile(pattern_def["pattern"])
            }
            self._compiled_patterns.append(compiled)

    def validate(
            self,
            code: str,
            file_path: Optional[str] = None,
            context: Optional[Dict[str, Any]] = None
    ) -> ValidationResult:
        """
        Valida código contra todas las reglas configuradas.

        Args:
            code: Código fuente a validar
            file_path: Ruta del archivo (para contexto)
            context: Metadata adicional para validadores personalizados

        Returns:
            ValidationResult con hallazgos y decisión de validez
        """
        findings: List[ValidationFinding] = []
        warnings: List[str] = []

        # Calcular hash del código
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]

        # 1. Validar patrones peligrosos
        findings.extend(self._check_patterns(code))

        # 2. Validar imports (si es código parseable)
        findings.extend(self._check_imports(code))

        # 3. Análisis AST para patrones complejos
        if self.language == "python":
            findings.extend(self._analyze_ast(code))

        # 4. Validar complejidad
        findings.extend(self._check_complexity(code))

        # 5. Ejecutar reglas personalizadas
        findings.extend(self._run_custom_rules(code, file_path, context))

        # 6. Filtrar por severidad configurada
        findings = self._filter_findings(findings, context)

        # Determinar validez
        has_blocking = any(f.severity in [Severity.CRITICAL, Severity.HIGH] for f in findings)

        # Agregar warnings informativos
        if not findings:
            warnings.append("✅ No se detectaron problemas de seguridad")

        return ValidationResult(
            valid=not has_blocking,
            findings=findings,
            warnings=warnings,
            code_hash=code_hash,
            language=self.language
        )

    def _check_patterns(self, code: str) -> List[ValidationFinding]:
        """Verifica patrones regex peligrosos"""
        findings = []

        for pattern_def in self._compiled_patterns:
            matches = pattern_def["compiled"].finditer(code)
            for match in matches:
                # Obtener línea y columna
                line_start = code[:match.start()].count('\n') + 1
                col_start = match.start() - code.rfind('\n', 0, match.start())

                # Obtener snippet de código
                line_end = code.find('\n', match.start())
                if line_end == -1:
                    line_end = len(code)
                snippet = code[match.start():line_end].strip()

                findings.append(ValidationFinding(
                    rule_name=pattern_def["name"],
                    severity=pattern_def["severity"],
                    message=pattern_def["message"],
                    line_number=line_start,
                    column=col_start,
                    code_snippet=snippet,
                    suggestion=pattern_def.get("suggestion"),
                    rule_type=ValidationRuleType.PATTERN
                ))

        return findings

    def _check_imports(self, code: str) -> List[ValidationFinding]:
        """Verifica imports peligrosos"""
        findings = []
        dangerous = self.DANGEROUS_IMPORTS.get(self.language, set())

        # Patrones de import por lenguaje
        import_patterns = {
            "python": [
                r'^\s*import\s+([\w.]+)',
                r'^\s*from\s+([\w.]+)\s+import',
            ],
            "javascript": [
                r'require\s*\(\s*["\']([^"\']+)["\']\s*\)',
                r'import\s+.*\s+from\s+["\']([^"\']+)["\']',
            ],
        }

        patterns = import_patterns.get(self.language, [])

        for pattern in patterns:
            for match in re.finditer(pattern, code, re.MULTILINE):
                module = match.group(1).split('.')[0]  # Módulo base

                # Verificar si está bloqueado
                if module in self.blocked_imports or module in dangerous:
                    # Permitir si está en allowlist
                    if module in self.allowed_imports:
                        continue

                    line = code[:match.start()].count('\n') + 1

                    findings.append(ValidationFinding(
                        rule_name="dangerous_import",
                        severity=Severity.MEDIUM,
                        message=f"Import de módulo potencialmente peligroso: {module}",
                        line_number=line,
                        code_snippet=match.group(0).strip(),
                        suggestion="Revisar si este import es necesario y usar alternativas seguras",
                        rule_type=ValidationRuleType.IMPORT_CHECK
                    ))

        return findings

    def _analyze_ast(self, code: str) -> List[ValidationFinding]:
        """Análisis AST para Python - patrones complejos"""
        findings = []

        if self.language != "python":
            return findings

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            findings.append(ValidationFinding(
                rule_name="syntax_error",
                severity=Severity.HIGH,
                message=f"Error de sintaxis: {e.msg}",
                line_number=e.lineno,
                suggestion="Corregir error de sintaxis antes de ejecutar",
                rule_type=ValidationRuleType.AST_ANALYSIS
            ))
            return findings

        # Analizar nodos del AST
        for node in ast.walk(tree):
            # Detectar llamadas peligrosas
            if isinstance(node, ast.Call):
                func_name = None

                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                elif isinstance(node.func, ast.Attribute):
                    func_name = node.func.attr

                if func_name in ['exec', 'eval', 'compile', '__import__']:
                    findings.append(ValidationFinding(
                        rule_name=f"dangerous_call_{func_name}",
                        severity=Severity.HIGH,
                        message=f"Llamada peligrosa: {func_name}()",
                        line_number=node.lineno,
                        suggestion="Evitar funciones que ejecutan código dinámico",
                        rule_type=ValidationRuleType.AST_ANALYSIS
                    ))

            # Detectar asignaciones a __builtins__
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id == '__builtins__':
                        findings.append(ValidationFinding(
                            rule_name="builtins_modification",
                            severity=Severity.CRITICAL,
                            message="Modificación de __builtins__ detectada",
                            line_number=node.lineno,
                            suggestion="No modificar builtins, puede romper el entorno",
                            rule_type=ValidationRuleType.AST_ANALYSIS
                        ))

        return findings

    def _check_complexity(self, code: str) -> List[ValidationFinding]:
        """Verifica métricas de complejidad"""
        findings = []

        # Contar líneas de código
        lines = [l for l in code.split('\n') if l.strip() and not l.strip().startswith('#')]

        if len(lines) > 1000:
            findings.append(ValidationFinding(
                rule_name="high_complexity",
                severity=Severity.LOW,
                message=f"Código muy largo: {len(lines)} líneas",
                suggestion="Considerar dividir en funciones/módulos más pequeños",
                rule_type=ValidationRuleType.COMPLEXITY
            ))

        # Detectar funciones muy largas (Python)
        if self.language == "python":
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        func_lines = node.end_lineno - node.lineno if hasattr(node, 'end_lineno') else 50
                        if func_lines > 100:
                            findings.append(ValidationFinding(
                                rule_name="long_function",
                                severity=Severity.LOW,
                                message=f"Función '{node.name}' muy larga: ~{func_lines} líneas",
                                line_number=node.lineno,
                                suggestion="Dividir función en partes más pequeñas",
                                rule_type=ValidationRuleType.COMPLEXITY
                            ))
            except:
                pass

        return findings

    def _run_custom_rules(
            self,
            code: str,
            file_path: Optional[str],
            context: Optional[Dict[str, Any]]
    ) -> List[ValidationFinding]:
        """Ejecuta reglas de validación personalizadas"""
        findings = []

        for rule in self.custom_rules:
            try:
                validator = rule.get("validator")
                if callable(validator):
                    result = validator(code, file_path, context or {})
                    if isinstance(result, ValidationFinding):
                        findings.append(result)
                    elif isinstance(result, list):
                        findings.extend([f for f in result if isinstance(f, ValidationFinding)])
            except Exception as e:
                logger.warning(f"Custom rule error: {e}")
                continue

        return findings

    def _filter_findings(
            self,
            findings: List[ValidationFinding],
            context: Optional[Dict[str, Any]]
    ) -> List[ValidationFinding]:
        """Filtra hallazgos según configuración de contexto"""
        if not context:
            return findings

        # Filtrar por severidad mínima permitida
        min_severity = context.get("min_severity", Severity.INFO)
        severity_order = [Severity.INFO, Severity.LOW, Severity.MEDIUM, Severity.HIGH, Severity.CRITICAL]

        min_index = severity_order.index(min_severity) if min_severity in severity_order else 0

        return [
            f for f in findings
            if severity_order.index(f.severity) >= min_index
        ]

    def add_custom_rule(
            self,
            name: str,
            validator: Callable[[str, Optional[str], Optional[Dict]], Any],
            default_severity: Severity = Severity.MEDIUM
    ) -> None:
        """Agrega una regla de validación personalizada"""
        self.custom_rules.append({
            "name": name,
            "validator": validator,
            "default_severity": default_severity
        })

    def get_rule_summary(self) -> Dict[str, Any]:
        """Genera resumen de reglas activas"""
        return {
            "language": self.language,
            "pattern_rules": len(self._compiled_patterns),
            "dangerous_imports": len(self.DANGEROUS_IMPORTS.get(self.language, set())),
            "custom_rules": len(self.custom_rules),
            "allowed_imports": list(self.allowed_imports),
            "blocked_imports": list(self.blocked_imports),
        }
