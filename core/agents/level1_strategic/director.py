from typing import Dict, Any, List

from ..base import BaseAgent, AgentLevel


class DirectorAgent(BaseAgent):
    """Director de Proyecto - Planificación y coordinación"""

    def __init__(self, **kwargs):
        super().__init__(
            name="Project Director",
            role="Project Director",
            goal="Planificar, estimar y coordinar el desarrollo de proyectos de software",
            backstory="""Eres un Director de Proyecto experimentado con 15+ años en la industria.
            Tu especialidad es transformar ideas vagas en planes de ejecución claros y realistas.
            Te enfocas en la viabilidad, estimación de tiempos y coordinación de equipos.""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de dirección de proyecto"""
        self._update_status('working')

        try:
            # Analizar tarea
            analysis = self._analyze_project_request(task, context)

            # Generar plan
            plan = self._create_project_plan(analysis)

            # Estimar viabilidad
            viability = self._assess_viability(plan)

            result = {
                'analysis': analysis,
                'plan': plan,
                'viability': viability,
                'recommendations': self._generate_recommendations(analysis, viability)
            }

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            raise e
        finally:
            self._update_status('idle')

    def _analyze_project_request(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Analiza la solicitud del proyecto"""
        prompt = f"""
        Como Director de Proyecto, analiza esta solicitud:

        SOLICITUD: {task}

        CONTEXTO: {context or 'Sin contexto adicional'}

        Proporciona un análisis estructurado con:
        1. Objetivo principal del proyecto
        2. Stakeholders identificados
        3. Requisitos funcionales clave
        4. Requisitos no funcionales clave
        5. Riesgos potenciales
        6. Dependencias externas
        7. Complejidad estimada (1-10)

        Responde en formato JSON.
        """

        response = self.llm.invoke(prompt)
        # Parsear JSON response
        return self._parse_json_response(response.content)

    def _create_project_plan(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Crea plan de proyecto con fases"""
        prompt = f"""
        Basado en este análisis, crea un plan de proyecto detallado:

        {analysis}

        El plan debe incluir:
        1. Fases del proyecto (mínimo 3)
        2. Duración estimada por fase (en horas/días)
        3. Entregables por fase
        4. Hitos clave
        5. Recursos necesarios

        Responde en formato JSON.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _assess_viability(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """Evalúa viabilidad del proyecto"""
        prompt = f"""
        Evalúa la viabilidad de este plan:

        {plan}

        Considera:
        1. Viabilidad técnica (0-100)
        2. Viabilidad de tiempo (0-100)
        3. Viabilidad de recursos (0-100)
        4. Score general de viabilidad (0-100)
        5. Principales obstáculos
        6. Recomendaciones para mejorar viabilidad

        Responde en formato JSON.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _generate_recommendations(self, analysis: Dict, viability: Dict) -> List[str]:
        """Genera recomendaciones basadas en análisis y viabilidad"""
        # Implementar lógica de recomendaciones
        return []

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM"""
        import json
        import re

        # Extraer JSON del contenido
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass

        # Fallback: retornar contenido raw
        return {'raw': content}