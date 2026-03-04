# devmind-core/core/agents/level3_execution/documenter.py
"""
DocumenterAgent - Generación de documentación y comentarios.

Responsable de:
- Escribir documentación de código
- Generar README y docs de proyecto
- Crear API documentation
- Mantener docs actualizadas
"""

from typing import Dict, Any, List, Optional
from ..base import BaseAgent, AgentLevel, AgentStatus


class DocumenterAgent(BaseAgent):
    """
    Documenter - Docs, comments, README, API docs.

    Nivel: EXECUTION (3)
    Especialidad: Documentación técnica, claridad, ejemplos
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente documenter.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Documenter Agent",
            role="Generador de Documentación",
            goal="Crear documentación clara, completa y mantenible para código y proyectos",
            backstory="""Eres un technical writer experto en documentación de software.
            Tu documentación es clara, concisa y útil para desarrolladores.
            Priorizas ejemplos prácticos, formato consistente y información
            que realmente ayuda a entender y usar el código.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de documentación"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_doc_task(task)

            if task_type == "readme":
                result = self._create_readme(task, context)
            elif task_type == "api":
                result = self._create_api_docs(task, context)
            elif task_type == "inline":
                result = self._create_inline_docs(task, context)
            elif task_type == "guide":
                result = self._create_guide(task, context)
            else:
                result = self._general_doc_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_doc_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de documentación"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["readme", "inicio", "introducción"]):
            return "readme"
        elif any(kw in task_lower for kw in ["api", "endpoints", "swagger", "openapi"]):
            return "api"
        elif any(kw in task_lower for kw in ["comentarios", "inline", "docstrings"]):
            return "inline"
        elif any(kw in task_lower for kw in ["guía", "tutorial", "how-to"]):
            return "guide"
        return "general"

    def _create_readme(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea documentación README"""
        project_type = context.get("project_type", "general")

        prompt = f"""
        Como documentador experto, crea un README para:

        SOLICITUD: {task}

        TIPO DE PROYECTO: {project_type}

        CONTEXTO: {context}

        REQUISITOS:
        - Título y descripción clara
        - Instalación paso a paso
        - Uso con ejemplos
        - Configuración
        - Contribución
        - License

        Proporciona README completo en Markdown.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        readme = self._parse_json_response(response.content)

        return {
            "content": readme.get("content", str(readme)),
            "readme_md": readme.get("markdown", ""),
            "success": True
        }

    def _create_api_docs(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea documentación de API"""
        format_type = context.get("format", "OpenAPI")

        prompt = f"""
        Como documentador experto, crea documentación de API para:

        SOLICITUD: {task}

        FORMATO: {format_type}

        CONTEXTO: {context}

        REQUISITOS:
        - Endpoints documentados
        - Request/response schemas
        - Ejemplos de uso
        - Authentication
        - Error codes

        Proporciona documentación completa de API.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        api_docs = self._parse_json_response(response.content)

        return {
            "content": api_docs.get("content", str(api_docs)),
            "api_docs": api_docs.get("documentation", ""),
            "success": True
        }

    def _create_inline_docs(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea documentación inline (comentarios/docstrings)"""
        code = context.get("code", "")
        language = context.get("language", "python")

        prompt = f"""
        Como documentador experto, agrega documentación inline para:

        SOLICITUD: {task}

        LENGUAJE: {language}

        CÓDIGO:
        {code if code else 'No proporcionado'}

        REQUISITOS:
        - Docstrings para clases y funciones
        - Comentarios explicativos
        - Type hints
        - Ejemplos en docstrings

        Proporciona código con documentación completa.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        docs = self._parse_json_response(response.content)

        return {
            "content": docs.get("content", str(docs)),
            "documented_code": docs.get("code", ""),
            "success": True
        }

    def _create_guide(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea guías/tutoriales"""
        prompt = f"""
        Como documentador experto, crea una guía para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Introducción clara
        - Prerrequisitos
        - Pasos detallados
        - Ejemplos de código
        - Troubleshooting
        - Recursos adicionales

        Proporciona guía completa en Markdown.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        guide = self._parse_json_response(response.content)

        return {
            "content": guide.get("content", str(guide)),
            "guide_md": guide.get("markdown", ""),
            "success": True
        }

    def _general_doc_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de documentación general"""
        prompt = f"""
        Como documentador experto, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona documentación completa y útil.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}