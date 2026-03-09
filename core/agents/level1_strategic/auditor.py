# devmind/core/agents/level1_strategic/auditor.py
"""
AuditorAgent - Auditor de Seguridad y Calidad de Código.

Responsable de:
- Revisar código en busca de vulnerabilidades
- Verificar cumplimiento de estándares
- Sugerir mejoras de calidad y mantenibilidad
- Generar reportes de auditoría
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, AgentLevel, AgentStatus


class AuditorAgent(BaseAgent):
    """
    Auditor de Seguridad y Calidad - Revisión técnica exhaustiva.

    Nivel: STRATEGIC (1)
    Especialidad: Seguridad, calidad, estándares, mejores prácticas
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
            goal="Revisar código y arquitecturas en busca de vulnerabilidades, problemas de calidad y desviaciones de estándares",
            backstory="""Eres un Auditor de Seguridad y Calidad con certificación en OWASP, 
            experiencia en code reviews a gran escala y conocimiento profundo de CWE, 
            OWASP Top 10, y estándares de codificación segura. Tu enfoque es preventivo:
            identificar riesgos antes de que se conviertan en incidentes. Eres meticuloso,
            objetivo y constructivo en tus recomendaciones.""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de auditoría"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_audit_task(task)

            if task_type == "security":
                result = self._security_audit(task, context)
            elif task_type == "quality":
                result = self._quality_audit(task, context)
            elif task_type == "compliance":
                result = self._compliance_check(task, context)
            elif task_type == "review":
                result = self._code_review(task, context)
            else:
                result = self._general_audit_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_audit_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de auditoría"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["seguridad", "vulnerabilidad", "owasp", "cwe", "inyección", "xss"]):
            return "security"
        elif any(kw in task_lower for kw in ["calidad", "mantenibilidad", "complejidad", "deuda técnica"]):
            return "quality"
        elif any(kw in task_lower for kw in ["estándar", "compliance", "norma", "política"]):
            return "compliance"
        elif any(kw in task_lower for kw in ["review", "revisar", "código", "pull request"]):
            return "review"
        return "general"

    def _security_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de seguridad"""
        prompt = f"""
        Como Auditor de Seguridad, analiza:

        SOLICITUD: {task}

        CÓDIGO/CONTEXTO: {context.get('code', context)}

        REQUISITOS:
        - Identificar vulnerabilidades OWASP Top 10 aplicables
        - Clasificar por severidad (Critical/High/Medium/Low)
        - Proporcionar PoC o escenario de explotación si aplica
        - Sugerir mitigaciones específicas y priorizadas
        - Referenciar CWE/CVE relevantes

        Proporciona reporte de seguridad en formato JSON estructurado.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        audit = self._parse_json_response(response.content)

        return {
            "content": audit.get("content", str(audit)),
            "findings": audit.get("findings", []),
            "severity_summary": audit.get("severity_summary"),
            "recommendations": audit.get("recommendations", []),
            "success": True
        }

    def _quality_audit(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza auditoría de calidad de código"""
        prompt = f"""
        Como Auditor de Calidad, evalúa:

        SOLICITUD: {task}

        CÓDIGO/CONTEXTO: {context.get('code', context)}

        REQUISITOS:
        - Métricas: complejidad ciclomática, acoplamiento, cohesión
        - Problemas: código duplicado, funciones largas, nombres poco claros
        - Deuda técnica estimada y priorización de refactor
        - Sugerencias de mejora específicas con ejemplos
        - Estimación de esfuerzo para correcciones

        Proporciona reporte de calidad en formato JSON estructurado.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        quality = self._parse_json_response(response.content)

        return {
            "content": quality.get("content", str(quality)),
            "metrics": quality.get("metrics", {}),
            "issues": quality.get("issues", []),
            "refactor_suggestions": quality.get("refactor_suggestions", []),
            "success": True
        }

    def _compliance_check(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Verifica cumplimiento de estándares"""
        prompt = f"""
        Como Auditor de Compliance, verifica:

        SOLICITUD: {task}

        ESTÁNDARES APLICABLES: {context.get('standards', ['PEP8', 'company_style_guide'])}

        CONTEXTO/CÓDIGO: {context.get('code', context)}

        REQUISITOS:
        - Listar desviaciones de cada estándar
        - Clasificar por impacto (blocking/warning/info)
        - Proporcionar correcciones específicas
        - Sugerir herramientas de linting/formatting apropiadas
        - Generar checklist de verificación

        Proporciona reporte de compliance en formato JSON estructurado.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        compliance = self._parse_json_response(response.content)

        return {
            "content": compliance.get("content", str(compliance)),
            "violations": compliance.get("violations", []),
            "checklist": compliance.get("checklist", []),
            "tools_recommendation": compliance.get("tools_recommendation"),
            "success": True
        }

    def _code_review(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Realiza code review constructivo"""
        prompt = f"""
        Como Auditor experto, realiza code review de:

        SOLICITUD: {task}

        CÓDIGO A REVISAR: {context.get('code', 'No proporcionado')}

        REQUISITOS:
        - Comentarios constructivos y específicos
        - Identificar bugs potenciales, edge cases no cubiertos
        - Sugerir mejoras de legibilidad y mantenibilidad
        - Validar tests y cobertura si aplica
        - Balancear crítica con reconocimiento de buenas prácticas

        Proporciona review en formato JSON con comentarios por línea/sección.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        review = self._parse_json_response(response.content)

        return {
            "content": review.get("content", str(review)),
            "comments": review.get("comments", []),
            "bugs_found": review.get("bugs_found", []),
            "improvements": review.get("improvements", []),
            "success": True
        }

    def _general_audit_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de auditoría general"""
        prompt = f"""
        Como Auditor experto, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona análisis técnico completo con hallazgos y recomendaciones.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}