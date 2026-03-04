# devmind-core/core/agents/level3_execution/tool_builder.py
"""
ToolBuilderAgent - Creación de herramientas CLI/API.

Responsable de:
- Crear herramientas CLI útiles
- Implementar APIs internas
- Automatizar tareas repetitivas
- Documentar herramientas creadas
"""

from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus


class ToolBuilderAgent(BaseAgent):
    """
    ToolBuilder - Crear herramientas CLI/API.

    Nivel: EXECUTION (3)
    Especialidad: Automatización, CLI, productividad
    """

    def __init__(self, **kwargs):
        """
        Inicializa el agente tool builder.

        Args:
            **kwargs: Parámetros para BaseAgent (model, temperature, etc.)
        """
        super().__init__(
            name="Tool Builder",
            role="Creador de Herramientas",
            goal="Crear herramientas CLI y APIs útiles que automaticen tareas repetitivas y mejoren la productividad",
            backstory="""Eres un desarrollador experto en crear herramientas de productividad.
            Tus herramientas son fáciles de usar, bien documentadas y resuelven
            problemas reales. Priorizas UX de CLI, manejo de errores claro
            y código reutilizable.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de creación de herramientas"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            task_type = self._classify_tool_task(task)

            if task_type == "cli":
                result = self._create_cli_tool(task, context)
            elif task_type == "api":
                result = self._create_api_tool(task, context)
            elif task_type == "script":
                result = self._create_script(task, context)
            elif task_type == "automation":
                result = self._create_automation(task, context)
            else:
                result = self._general_tool_task(task, context)

            self.tasks_completed += 1
            return result

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)

    def _classify_tool_task(self, task: str) -> str:
        """Clasifica el tipo de tarea de herramienta"""
        task_lower = task.lower()

        if any(kw in task_lower for kw in ["cli", "command", "terminal", "consola"]):
            return "cli"
        elif any(kw in task_lower for kw in ["api", "endpoint", "rest", "webhook"]):
            return "api"
        elif any(kw in task_lower for kw in ["script", "bash", "python", "automatizar"]):
            return "script"
        elif any(kw in task_lower for kw in ["automation", "workflow", "pipeline"]):
            return "automation"
        return "general"

    def _create_cli_tool(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea herramienta CLI"""
        language = context.get("language", "python")

        prompt = f"""
        Como creador de herramientas, crea una CLI para:

        SOLICITUD: {task}

        LENGUAJE: {language}

        REQUISITOS:
        - Argumentos bien definidos (argparse/click)
        - Help messages claros
        - Manejo de errores apropiado
        - Exit codes apropiados
        - Ejemplos de uso en help

        Proporciona código completo de la CLI.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        cli_tool = self._parse_json_response(response.content)

        return {
            "content": cli_tool.get("content", str(cli_tool)),
            "cli_code": cli_tool.get("code", ""),
            "usage_example": cli_tool.get("usage", ""),
            "success": True
        }

    def _create_api_tool(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea herramienta API"""
        framework = context.get("framework", "FastAPI")

        prompt = f"""
        Como creador de herramientas, crea una API para:

        SOLICITUD: {task}

        FRAMEWORK: {framework}

        REQUISITOS:
        - Endpoints bien diseñados
        - Validación de inputs
        - Error handling
        - Documentation automática
        - Tests básicos

        Proporciona código completo de la API.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        api_tool = self._parse_json_response(response.content)

        return {
            "content": api_tool.get("content", str(api_tool)),
            "api_code": api_tool.get("code", ""),
            "success": True
        }

    def _create_script(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea script de automatización"""
        language = context.get("language", "python")

        prompt = f"""
        Como creador de herramientas, crea un script para:

        SOLICITUD: {task}

        LENGUAJE: {language}

        REQUISITOS:
        - Script ejecutable
        - Configuración vía env vars o config file
        - Logging apropiado
        - Manejo de errores
        - Instrucciones de uso

        Proporciona código completo del script.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        script = self._parse_json_response(response.content)

        return {
            "content": script.get("content", str(script)),
            "script_code": script.get("code", ""),
            "success": True
        }

    def _create_automation(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Crea automatización/workflow"""
        prompt = f"""
        Como creador de herramientas, crea automatización para:

        SOLICITUD: {task}

        CONTEXTO: {context}

        REQUISITOS:
        - Workflow completo
        - Triggers apropiados
        - Error handling y retries
        - Logging y monitoring
        - Documentación del workflow

        Proporciona código completo de automatización.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        automation = self._parse_json_response(response.content)

        return {
            "content": automation.get("content", str(automation)),
            "automation_code": automation.get("code", ""),
            "success": True
        }

    def _general_tool_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Tarea de herramienta general"""
        prompt = f"""
        Como creador de herramientas, responde:

        SOLICITUD: {task}

        CONTEXTO: {context}

        Proporciona una solución técnica completa con código si es necesario.
        Responde en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        result = self._parse_json_response(response.content)

        return {"content": result.get("content", str(result)), "success": True}