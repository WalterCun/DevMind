# devmind-core/core/agents/level3_execution/coder.py
"""
CoderAgent - Generación y refactorización de código.

Responsable de:
- Escribir código limpio y funcional
- Refactorizar código existente
- Implementar features específicas
- Seguir mejores prácticas
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, AgentLevel, AgentStatus


class CoderAgent(BaseAgent):
    """
    Coder - Generación de código, refactor, snippets.

    Nivel: EXECUTION (3)
    Especialidad: Implementación, código limpio, mejores prácticas
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente coder.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Coder Agent",
            role="Generador de Código",
            goal="Escribir código limpio, funcional, testeable y bien documentado según especificaciones",
            backstory="""Eres un desarrollador experto en múltiples lenguajes de programación.
            Tu código sigue principios SOLID, es legible, mantenible y eficiente.
            Priorizas código limpio sobre código inteligente. Documentas adecuadamente
            y escribes código que otros desarrolladores pueden entender fácilmente.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de codificación"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_coding_task(task)

            if task_type == "create":
                result = self._create_code(task, context)
            elif task_type == "refactor":
                result = self._refactor_code(task, context)
            elif task_type == "fix":
                result = self._fix_bug(task, context)
            elif task_type == "implement":
                result = self._implement_feature(task, context)
            else:
                result = self._general_coding_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_coding_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de coding"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["crear", "create", "nuevo", "escribir"]):
            return "create"
        elif any(kw in task_lower for kw in ["refactor", "refactorizar", "mejorar", "limpiar"]):
            return "refactor"
        elif any(kw in task_lower for kw in ["fix", "corregir", "bug", "error", "arreglar"]):
            return "fix"
        elif any(kw in task_lower for kw in ["implementar", "feature", "funcionalidad"]):
            return "implement"
        return "general"

    def _create_code(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea código nuevo"""
        language = context.get("language", "python")
        framework = context.get("framework", "")

        prompt = f"""
        Como desarrollador experto, crea código para:

        SOLICITUD: {task}

        LENGUAJE: {language}
        FRAMEWORK: {framework if framework else 'N/A'}

        REQUISITOS:
        - Código limpio y legible
        - Type hints completos
        - Docstrings apropiados
        - Manejo de errores
        - Tests básicos incluidos

        Proporciona código completo listo para usar.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        code_result = self._parse_json_response(response.content)

        return {
            "content": code_result.get("content", str(code_result)),
            "code": code_result.get("code", ""),
            "language": language,
            "filename": code_result.get("filename", ""),
            "success": True
        }

    def _refactor_code(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refactoriza código existente"""
        code = context.get("code", "")

        prompt = f"""
        Como desarrollador experto, refactoriza este código:

        SOLICITUD: {task}

        CÓDIGO ORIGINAL:
        {code if code else 'No proporcionado'}

        REQUISITOS:
        - Mejorar legibilidad
        - Reducir complejidad
        - Aplicar principios SOLID
        - Extraer funciones/métodos
        - Mejorar nombres

        Proporciona código refactorizado con explicación de cambios.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        refactor_result = self._parse_json_response(response.content)

        return {
            "content": refactor_result.get("content", str(refactor_result)),
            "refactored_code": refactor_result.get("code", ""),
            "changes": refactor_result.get("changes", []),
            "success": True
        }

    def _fix_bug(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Corrige bugs"""
        code = context.get("code", "")
        error = context.get("error", "")

        prompt = f"""
        Como desarrollador experto, corrige este bug:

        SOLICITUD: {task}

        CÓDIGO:
        {code if code else 'No proporcionado'}

        ERROR:
        {error if error else 'No proporcionado'}

        REQUISITOS:
        - Identificar causa raíz
        - Corregir sin romper funcionalidad existente
        - Agregar tests para el bug
        - Explicar la solución

        Proporciona código corregido completo.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        fix_result = self._parse_json_response(response.content)

        return {
            "content": fix_result.get("content", str(fix_result)),
            "fixed_code": fix_result.get("code", ""),
            "root_cause": fix_result.get("root_cause", ""),
            "success": True
        }

    def _implement_feature(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implementa features"""
        prompt = f"""
        Como desarrollador experto, implementa esta feature:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Implementación completa
        - Integración con código existente
        - Tests incluidos
        - Documentación

        Proporciona código completo de la feature.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        feature_result = self._parse_json_response(response.content)

        return {
            "content": feature_result.get("content", str(feature_result)),
            "code": feature_result.get("code", ""),
            "success": True
        }

    def _general_coding_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de coding general"""
        prompt = f"""
        Como desarrollador experto, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}