# devmind-core/core/agents/level2_specialist/qa.py
"""
QASpecialistAgent - Especialista en testing y calidad.

Responsable de:
- Escribir tests unitarios y de integración
- Asegurar coverage de código
- Automatizar QA
- Validar calidad del código
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class QASpecialistAgent(BaseAgent):
    """
    Especialista QA - Testing, TDD, coverage, automation.

    Nivel: SPECIALIST (2)
    Especialidad: Tests, calidad, automatización, CI
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente especialista QA.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="QA Specialist",
            role="QA Specialist",
            goal="Escribir tests efectivos, asegurar coverage y automatizar procesos de QA",
            backstory="""Eres un ingeniero de QA experto en testing unitario, de integración y e2e.
            Tu filosofía es TDD: tests primero, código después. Priorizas tests legibles,
            aislados, rápidos y con buen coverage de casos edge. Conoces pytest, unittest,
            Jest, Cypress y herramientas modernas de testing.""",
            level=AgentLevel.SPECIALIST,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de QA"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_qa_task(task)

            if task_type == "unit":
                result = self._create_unit_tests(task, context)
            elif task_type == "integration":
                result = self._create_integration_tests(task, context)
            elif task_type == "e2e":
                result = self._create_e2e_tests(task, context)
            elif task_type == "coverage":
                result = self._analyze_coverage(task, context)
            else:
                result = self._general_qa_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_qa_task(self, task: str) -> str:
        """Clasifica el tipo de tarea QA"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["unit", "unitario", "pytest", "unittest"]):
            return "unit"
        elif any(kw in task_lower for kw in ["integración", "integration", "api", "endpoint"]):
            return "integration"
        elif any(kw in task_lower for kw in ["e2e", "end-to-end", "cypress", "selenium", "navegador"]):
            return "e2e"
        elif any(kw in task_lower for kw in ["coverage", "cobertura", "reporte"]):
            return "coverage"
        return "general"

    def _create_unit_tests(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea tests unitarios"""
        framework = context.get("framework", "pytest")
        language = context.get("language", "python")

        prompt = f"""
        Como especialista QA, crea tests unitarios para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}
        LENGUAJE: {language}

        CÓDIGO A TESTEAR:
        {context.get('code', 'No proporcionado')}

        REQUISITOS:
        - Tests aislados e independientes
        - Mocks apropiados para dependencias
        - Coverage de casos edge
        - Assertions claros y descriptivos
        - Fixtures reutilizables

        Proporciona código completo de tests.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        tests = self._parse_json_response(response.content)

        return {
            "content": tests.get("content", str(tests)),
            "test_code": tests.get("code", ""),
            "framework": framework,
            "success": True
        }

    def _create_integration_tests(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea tests de integración"""
        prompt = f"""
        Como especialista QA, crea tests de integración para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Tests de API/endpoints
        - Database transactions
        - External service mocks
        - Setup/teardown apropiado
        - Validación de respuestas

        Proporciona código completo de tests.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        tests = self._parse_json_response(response.content)

        return {
            "content": tests.get("content", str(tests)),
            "test_code": tests.get("code", ""),
            "success": True
        }

    def _create_e2e_tests(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea tests end-to-end"""
        framework = context.get("framework", "Cypress")

        prompt = f"""
        Como especialista QA, crea tests e2e para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        REQUISITOS:
        - Flujos de usuario completos
        - Selectores robustos
        - Esperas apropiadas
        - Datos de test
        - Screenshots en fallos

        Proporciona código completo de tests e2e.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        tests = self._parse_json_response(response.content)

        return {
            "content": tests.get("content", str(tests)),
            "test_code": tests.get("code", ""),
            "framework": framework,
            "success": True
        }

    def _analyze_coverage(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza coverage de tests"""
        prompt = f"""
        Como especialista QA, analiza el coverage para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona:
        1. Coverage actual estimado
        2. Líneas/functionsin testeadas
        3. Tests faltantes recomendados
        4. Priority de tests a agregar
        5. Configuración de coverage tools

        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        analysis = self._parse_json_response(response.content)

        return {
            "content": analysis.get("content", str(analysis)),
            "coverage_analysis": analysis,
            "recommendations": analysis.get("recommendations", []),
            "success": True
        }

    def _general_qa_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea QA general"""
        prompt = f"""
        Como especialista QA, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}