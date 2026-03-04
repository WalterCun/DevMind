# devmind-core/core/agents/level3_execution/tester.py
"""
TesterAgent - Creación de tests unitarios y de integración.

Responsable de:
- Escribir tests unitarios
- Crear tests de integración
- Automatizar testing
- Validar calidad
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class TesterAgent(BaseAgent):
    """
    Tester - Tests unitarios, integración, e2e.

    Nivel: EXECUTION (3)
    Especialidad: Testing automatizado, QA, validation
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente tester.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Tester Agent",
            role="Tester Agent",
            goal="Escribir tests efectivos que validen funcionalidad y prevengan regresiones",
            backstory="""Eres un ingeniero de testing experto en pytest, unittest y frameworks modernos.
            Tu enfoque es TDD: tests primero. Escribes tests legibles, aislados,
            rápidos y con buen coverage de casos edge. Priorizas tests que documentan
            el comportamiento esperado del código.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de testing"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_test_task(task)

            if task_type == "unit":
                result = self._create_unit_tests(task, context)
            elif task_type == "integration":
                result = self._create_integration_tests(task, context)
            elif task_type == "fixture":
                result = self._create_fixtures(task, context)
            elif task_type == "mock":
                result = self._create_mocks(task, context)
            else:
                result = self._general_test_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_test_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de testing"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["unit", "unitario", "clase", "función"]):
            return "unit"
        elif any(kw in task_lower for kw in ["integración", "integration", "api", "db"]):
            return "integration"
        elif any(kw in task_lower for kw in ["fixture", "setup", "datos de test"]):
            return "fixture"
        elif any(kw in task_lower for kw in ["mock", "stub", "fake"]):
            return "mock"
        return "general"

    def _create_unit_tests(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea tests unitarios"""
        framework = context.get("framework", "pytest")
        code = context.get("code", "")

        prompt = f"""
        Como tester experto, crea tests unitarios para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        CÓDIGO A TESTEAR:
        {code if code else 'No proporcionado'}

        REQUISITOS:
        - Una aserción por test
        - Nombres descriptivos (test_should_...)
        - Mocks para dependencias externas
        - Coverage de casos happy path y edge cases
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
        Como tester experto, crea tests de integración para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Tests de endpoints/API
        - Database transactions con rollback
        - External services mocked
        - Setup/teardown apropiado
        - Validación de respuestas completas

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

    def _create_fixtures(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea fixtures para tests"""
        prompt = f"""
        Como tester experto, crea fixtures para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Fixtures modulares y reutilizables
        - Datos de test realistas
        - Setup/teardown eficiente
        - Parametrización si aplica

        Proporciona código completo de fixtures.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        fixtures = self._parse_json_response(response.content)

        return {
            "content": fixtures.get("content", str(fixtures)),
            "fixture_code": fixtures.get("code", ""),
            "success": True
        }

    def _create_mocks(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea mocks para tests"""
        prompt = f"""
        Como tester experto, crea mocks para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Mocks apropiados para dependencias
        - Comportamiento configurado
        - Verificación de llamadas
        - Clear/reset entre tests

        Proporciona código completo de mocks.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        mocks = self._parse_json_response(response.content)

        return {
            "content": mocks.get("content", str(mocks)),
            "mock_code": mocks.get("code", ""),
            "success": True
        }

    def _general_test_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de testing general"""
        prompt = f"""
        Como tester experto, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}