# devmind/core/agents/level1_strategic/architect.py
"""
ArchitectAgent - Arquitecto Principal de Software.

Responsable de:
- Diseñar arquitecturas escalables y mantenibles
- Evaluar tecnologías y frameworks
- Documentar decisiones arquitectónicas (ADRs)
- Establecer patrones y estándares de código
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, AgentLevel, AgentStatus


class ArchitectAgent(BaseAgent):
    """
    Arquitecto Principal - Diseño técnico y decisiones fundamentales.

    Nivel: STRATEGIC (1)
    Especialidad: Arquitectura, patrones, evaluación tecnológica
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente arquitecto.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Architect Principal",
            role="Architect Principal",
            goal="Diseñar arquitecturas escalables, evaluar tecnologías y documentar decisiones técnicas fundamentales",
            backstory="""Eres un Arquitecto de Software senior con 20+ años de experiencia.
            Has liderado arquitecturas para sistemas de alto tráfico y misión crítica.
            Tu enfoque es pragmático: soluciones simples que escalen, documentación clara,
            y decisiones basadas en evidencia. Dominas patrones de diseño, microservicios,
            event-driven architecture, y evaluación objetiva de tecnologías.""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de arquitectura"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_architecture_task(task)

            if task_type == "design":
                result = self._design_architecture(task, context)
            elif task_type == "evaluate":
                result = self._evaluate_technology(task, context)
            elif task_type == "adr":
                result = self._create_adr(task, context)
            elif task_type == "patterns":
                result = self._recommend_patterns(task, context)
            else:
                result = self._general_architecture_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_architecture_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de arquitectura"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["diseñar", "arquitectura", "estructura", "diagrama"]):
            return "design"
        elif any(kw in task_lower for kw in ["evaluar", "comparar", "tecnología", "framework", "librería"]):
            return "evaluate"
        elif any(kw in task_lower for kw in ["decisión", "adr", "documentar", "registro"]):
            return "adr"
        elif any(kw in task_lower for kw in ["patrón", "pattern", "mejor práctica", "estándar"]):
            return "patterns"
        return "general"

    def _design_architecture(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña arquitectura de sistema"""
        prompt = f"""
        Como Arquitecto Principal, diseña una arquitectura para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Diagrama de componentes de alto nivel
        - Flujos de datos principales
        - Puntos de integración externa
        - Estrategia de escalabilidad
        - Consideraciones de seguridad
        - Tecnologías recomendadas con justificación

        Proporciona la arquitectura en formato estructurado JSON.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        design = self._parse_json_response(response.content)

        return {
            "content": design.get("content", str(design)),
            "architecture": design,
            "diagrams": design.get("diagrams", []),
            "success": True
        }

    def _evaluate_technology(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa tecnologías para caso de uso específico"""
        prompt = f"""
        Como Arquitecto Principal, evalúa tecnologías para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Comparativa de 3-5 opciones relevantes
        - Pros y contras de cada una
        - Criterios: rendimiento, mantenibilidad, comunidad, costos
        - Recomendación final con justificación
        - Riesgos y mitigaciones

        Proporciona evaluación en formato estructurado JSON.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        evaluation = self._parse_json_response(response.content)

        return {
            "content": evaluation.get("content", str(evaluation)),
            "evaluation": evaluation,
            "recommendation": evaluation.get("recommendation"),
            "success": True
        }

    def _create_adr(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea Architectural Decision Record (ADR)"""
        prompt = f"""
        Como Arquitecto Principal, documenta una decisión arquitectónica:

        SOLICITUD: {task}

        CONTEXTO: {context}

        FORMATO ADR:
        - Título: Decisión clara y concisa
        - Estado: Proposed/Accepted/Deprecated/Superseded
        - Contexto: Situación y fuerzas que motivan la decisión
        - Decisión: Qué se decidió y por qué
        - Consecuencias: Impactos positivos y negativos
        - Alternativas consideradas: Otras opciones evaluadas
        - Referencias: Links a documentación relevante

        Proporciona ADR completo en formato JSON.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        adr = self._parse_json_response(response.content)

        return {
            "content": adr.get("content", str(adr)),
            "adr": adr,
            "adr_id": adr.get("id"),
            "success": True
        }

    def _recommend_patterns(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Recomienda patrones de diseño/arquitectura"""
        prompt = f"""
        Como Arquitecto Principal, recomienda patrones para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Patrones aplicables al problema
        - Cuándo usar cada patrón
        - Cuándo NO usar cada patrón
        - Ejemplos de implementación
        - Anti-patrones a evitar

        Proporciona recomendaciones en formato estructurado JSON.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        patterns = self._parse_json_response(response.content)

        return {
            "content": patterns.get("content", str(patterns)),
            "patterns": patterns,
            "success": True
        }

    def _general_architecture_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de arquitectura general"""
        prompt = f"""
        Como Arquitecto Principal, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución arquitectónica completa con justificación técnica.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}