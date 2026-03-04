# devmind-core/core/agents/level1_strategic/auditor.py
"""
AuditorAgent - Auditor de Seguridad y Calidad de Código.

Responsable de:
- Revisar código en busca de vulnerabilidades
- Validar cumplimiento de estándares
- Detectar code smells y anti-patrones
- Generar reportes de auditoría
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class AuditorAgent(BaseAgent):
    """
    Auditor de Seguridad y Calidad - Revisión técnica profunda.

    Nivel: STRATEGIC (1)
    Especialidad: Seguridad, estándares, code review, compliance
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente auditor.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Security Auditor",
            role="Security Auditor",
            goal="Revisar código, detectar vulnerabilidades y asegurar cumplimiento de estándares de calidad",
            backstory="""Eres un Auditor de Seguridad Senior con experiencia en revisión de código,
            análisis estático y detección de vulnerabilidades. Tu enfoque es meticuloso:
            revisas cada línea, validas contra OWASP Top 10, y aseguras que el código
            cumpla con mejores prácticas de la industria. Eres conservador por diseño.""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta tareas de auditoría de código.

        Args:
            task: Descripción de la tarea de auditoría
            context: Contexto adicional (código, estándares, etc.)

        Returns:
            Dict con hallazgos, severidad y recomendaciones
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Clasificar tipo de auditoría
            audit_type = self._classify_audit_task(task)

            if audit_type == "security":
                result = self._security_audit(task, context)
            elif audit_type == "quality":
                result = self._quality_audit(task, context)
            elif audit_type == "compliance":
                result = self._compliance_audit(task, context)
            elif audit_type == "review":
                result = self._code_review(task, context)
            else:
                result = self._general_audit(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {
                "error": str(e),
                "success": False,
                "task": task
            }
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_audit_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de auditoría"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["seguridad", "vulnerabilidad", "owasp", "inyección", "xss", "auth"]):
            return "security"
        elif any(kw in task_lower for kw in ["calidad", "pep8", "estándar", "clean code", "smell"]):
            return "quality"
        elif any(kw in task_lower for kw in ["compliance", "gdpr", "hipaa", "normativa", "regulación"]):
            return "compliance"
        elif any(kw in task_lower for kw in ["revisar", "review", "pull request", "merge"]):
            return "review"
        else:
            return "general"

    def _security_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de seguridad"""
        code = context.get("code", context.get("content", ""))

        prompt = f"""
        Como Auditor de Seguridad, revisa este código en busca de vulnerabilidades:

        SOLICITUD: {task}

        CÓDIGO A AUDITAR:
        {code if code else "No proporcionado"}

        CONTEXTO ADICIONAL:
        {context}

        Realiza una revisión de seguridad con:
        1. Vulnerabilidades detectadas (OWASP Top 10)
        2. Nivel de severidad para cada hallazgo (CRITICAL/HIGH/MEDIUM/LOW)
        3. Línea/ubicación aproximada del problema
        4. Explicación técnica del riesgo
        5. Recomendación de fix específica
        6. Score de seguridad general (0-100)

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "security_audit": audit,
            "vulnerabilities": audit.get("vulnerabilities", []),
            "security_score": audit.get("security_score"),
            "success": True
        }

    def _quality_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de calidad de código"""
        code = context.get("code", context.get("content", ""))

        prompt = f"""
        Como Auditor de Calidad, revisa este código contra estándares:

        SOLICITUD: {task}

        CÓDIGO A REVISAR:
        {code if code else "No proporcionado"}

        CONTEXTO:
        {context}

        Proporciona una evaluación de calidad con:
        1. Code smells detectados
        2. Violaciones de principios (SOLID, DRY, KISS)
        3. Complejidad ciclomática estimada
        4. Legibilidad y mantenibilidad (score 0-100)
        5. Recomendaciones de refactorización priorizadas
        6. Cumplimiento de convenciones (PEP8, etc.)

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "quality_audit": audit,
            "code_smells": audit.get("code_smells", []),
            "quality_score": audit.get("quality_score"),
            "success": True
        }

    def _compliance_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de cumplimiento normativo"""
        prompt = f"""
        Como Auditor de Compliance, evalúa cumplimiento normativo:

        SOLICITUD: {task}

        CONTEXTO DEL SISTEMA:
        {context}

        Considera regulaciones relevantes:
        - GDPR (protección de datos personales)
        - HIPAA (si aplica a salud)
        - PCI-DSS (si aplica a pagos)
        - Normativas locales de tu región

        Proporciona:
        1. Regulaciones aplicables identificadas
        2. Puntos de cumplimiento verificados
        3. Brechas de compliance detectadas
        4. Recomendaciones para alcanzar compliance
        5. Checklist de verificación

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "compliance_audit": audit,
            "applicable_regulations": audit.get("regulations", []),
            "compliance_score": audit.get("compliance_score"),
            "success": True
        }

    def _code_review(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza code review tradicional"""
        code = context.get("code", context.get("content", ""))
        diff = context.get("diff", "")

        prompt = f"""
        Como Auditor Senior, realiza un code review:

        SOLICITUD: {task}

        CÓDIGO:
        {code if code else diff if diff else "No proporcionado"}

        CONTEXTO:
        {context}

        Proporciona un review estructurado con:
        1. Resumen ejecutivo del cambio
        2. Puntos fuertes del código
        3. Problemas detectados (con severidad)
        4. Sugerencias de mejora
        5. Veredicto: APPROVE | REQUEST_CHANGES | COMMENT
        6. Comentarios específicos por línea (si aplica)

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        review = self._parse_json_response(response.content)

        return {
            "content": review.get("content", str(review)),
            "code_review": review,
            "verdict": review.get("verdict"),
            "comments": review.get("comments", []),
            "success": True
        }

    def _general_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Auditoría general cuando no se clasifica específicamente"""
        prompt = f"""
        Como Auditor, responde esta consulta de auditoría:

        CONSULTA: {task}

        CONTEXTO:
        {context}

        Proporciona una respuesta técnica completa con:
        1. Análisis del riesgo/problema
        2. Hallazgos principales
        3. Recomendaciones accionables
        4. Priorización de acciones

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "audit": audit,
            "success": True
        }