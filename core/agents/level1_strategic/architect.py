# devmind-core/core/agents/level1_strategic/architect.py
"""
ArchitectAgent - Arquitecto Principal de Software.

Responsable de:
- Diseñar arquitectura de sistemas
- Evaluar tecnologías y patrones
- Documentar decisiones arquitectónicas (ADRs)
- Validar coherencia técnica del proyecto
"""

from datetime import datetime
from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class ArchitectAgent(BaseAgent):
    """
    Arquitecto Principal - Diseño y evaluación técnica.

    Nivel: STRATEGIC (1)
    Especialidad: Patrones, tecnologías, ADRs, coherencia arquitectónica
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
            backstory="""Eres un Arquitecto de Software Senior con 20+ años de experiencia 
            diseñando sistemas distribuidos, microservicios y aplicaciones enterprise.
            Tu enfoque es pragmático: priorizas mantenibilidad, escalabilidad y simplicidad.
            Documentas cada decisión importante como ADR (Architecture Decision Record).""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta tareas de arquitectura de software.

        Args:
            task: Descripción de la tarea arquitectónica
            context: Contexto adicional (stack, restricciones, etc.)

        Returns:
            Dict con análisis, recomendaciones y ADRs generados
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Clasificar tipo de tarea arquitectónica
            task_type = self._classify_architecture_task(task)

            if task_type == "design":
                result = self._design_architecture(task, context)
            elif task_type == "evaluate":
                result = self._evaluate_technology(task, context)
            elif task_type == "adr":
                result = self._create_adr(task, context)
            elif task_type == "review":
                result = self._review_architecture(task, context)
            else:
                result = self._general_architecture_consultation(task, context)

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

    def _classify_architecture_task(self, task: str) -> str:
        """Clasifica el tipo de tarea arquitectónica"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["diseñar", "arquitectura", "estructura", "patron"]):
            return "design"
        elif any(kw in task_lower for kw in ["evaluar", "comparar", "tecnología", "stack", "librería"]):
            return "evaluate"
        elif any(kw in task_lower for kw in ["decisión", "adr", "documentar", "registro"]):
            return "adr"
        elif any(kw in task_lower for kw in ["revisar", "auditar", "validar", "coherencia"]):
            return "review"
        else:
            return "general"

    def _design_architecture(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña arquitectura de sistema"""
        prompt = f"""
        Como Arquitecto Principal, diseña una arquitectura para:

        SOLICITUD: {task}

        CONTEXTO TÉCNICO:
        {context.get('tech_stack', 'No especificado')}

        RESTRICCIONES:
        {context.get('constraints', 'Ninguna especificada')}

        Proporciona un diseño estructurado con:
        1. Estilo arquitectónico recomendado (monolito, microservicios, event-driven, etc.)
        2. Diagrama de componentes en formato texto (Mermaid o descripción)
        3. Tecnologías clave por capa (frontend, backend, datos, infra)
        4. Patrones de diseño aplicados y justificación
        5. Consideraciones de escalabilidad y resiliencia
        6. Puntos de extensión futuros

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        design = self._parse_json_response(response.content)

        return {
            "content": design.get("content", str(design)),
            "architecture_design": design,
            "recommendations": design.get("recommendations", []),
            "success": True
        }

    def _evaluate_technology(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa tecnologías o stacks"""
        prompt = f"""
        Como Arquitecto Principal, evalúa esta tecnología/stack:

        SOLICITUD: {task}

        CRITERIOS DE EVALUACIÓN:
        - Madurez y comunidad
        - Rendimiento y escalabilidad
        - Curva de aprendizaje
        - Costo total de propiedad
        - Compatibilidad con stack actual: {context.get('current_stack', 'N/A')}

        Proporciona:
        1. Score general (0-100)
        2. Pros y contras estructurados
        3. Casos de uso ideales
        4. Alternativas a considerar
        5. Recomendación final con justificación

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        evaluation = self._parse_json_response(response.content)

        return {
            "content": evaluation.get("content", str(evaluation)),
            "technology_evaluation": evaluation,
            "recommendation": evaluation.get("recommendation"),
            "score": evaluation.get("score"),
            "success": True
        }

    def _create_adr(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea Architecture Decision Record (ADR)"""
        prompt = f"""
        Como Arquitecto Principal, documenta esta decisión arquitectónica:

        TÍTULO: {task}

        CONTEXTO:
        {context.get('context', 'No especificado')}

        Genera un ADR completo con:
        1. Title: Título claro de la decisión
        2. Status: proposed | accepted | deprecated | superseded
        3. Context: Situación que motivó la decisión
        4. Decision: Decisión tomada (clara y accionable)
        5. Consequences: 
           - Positivas (beneficios)
           - Negativas (trade-offs)
           - Neutrales (impactos laterales)
        6. Alternatives: Opciones consideradas y por qué se rechazaron
        7. Compliance: Cómo se verificará que se cumple la decisión

        Formato de salida JSON válido.
        """

        response = self.llm.invoke(prompt)
        adr = self._parse_json_response(response.content)

        return {
            "content": adr.get("content", str(adr)),
            "adr": adr,
            "adr_id": f"ADR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            "success": True
        }

    def _review_architecture(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Revisa arquitectura existente"""
        prompt = f"""
        Como Arquitecto Principal, revisa esta arquitectura:

        DESCRIPCIÓN: {task}

        DIAGRAMA/CÓDIGO:
        {context.get('architecture_description', 'No proporcionado')}

        Realiza una revisión técnica con:
        1. Puntos fuertes identificados
        2. Riesgos arquitectónicos detectados
        3. Violaciones de principios (SOLID, 12-factor, etc.)
        4. Recomendaciones de mejora priorizadas (crítico/alto/medio/bajo)
        5. Métricas sugeridas para monitorear salud arquitectónica

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        review = self._parse_json_response(response.content)

        return {
            "content": review.get("content", str(review)),
            "architecture_review": review,
            "risks": review.get("risks", []),
            "recommendations": review.get("recommendations", []),
            "success": True
        }

    def _general_architecture_consultation(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Consulta arquitectónica general"""
        prompt = f"""
        Como Arquitecto Principal, responde esta consulta:

        CONSULTA: {task}

        CONTEXTO ADICIONAL:
        {context}

        Proporciona una respuesta técnica completa con:
        1. Análisis del problema
        2. Opciones de solución
        3. Recomendación con justificación
        4. Próximos pasos sugeridos

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        consultation = self._parse_json_response(response.content)

        return {
            "content": consultation.get("content", str(consultation)),
            "consultation": consultation,
            "success": True
        }