# core/agents/level3_execution/coder.py
"""
CoderAgent - Generación y refactorización de código con razonamiento estructurado.
"""

import json
import logging
import re
from typing import Dict, Any

from ..base import BaseAgent, AgentLevel, AgentStatus

logger = logging.getLogger(__name__)


class CoderAgent(BaseAgent):
    """
    Coder - Generación de código con capacidad de planificación autónoma.
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Coder Agent",
            role="Coder Agent",
            goal="Escribir código limpio, funcional, testeable y bien documentado según especificaciones",
            backstory="""Eres un desarrollador experto en múltiples lenguajes de programación.
            Tu código sigue principios SOLID, es legible, mantenible y eficiente.
            Priorizas código limpio sobre código inteligente. Documentas adecuadamente
            y escribes código que otros desarrolladores pueden entender fácilmente.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta tareas de codificación con razonamiento"""
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Prompt de Sistema con estructura ReAct
            system_prompt = """
Eres un Ingeniero de Software Senior especializado en desarrollo autónomo.
Tu proceso de trabajo es ESTRICTO:

1. ANALIZA: Lee el contexto del proyecto proporcionado.
2. PLANIFICA: Desglosa la tarea en pasos pequeños y atómicos.
3. EJECUTA: Usa las herramientas disponibles (write_file, run_command) para implementar UN SOLO PASO a la vez.
4. VERIFICA: Después de cada acción, observa el resultado.

REGLAS DE ORO:
- NUNCA escribas código sin verificar si el archivo ya existe.
- Si encuentras un error, analiza el traceback ANTES de intentar corregirlo.
- Si instalas dependencias, usa comandos específicos (ej: pip install numpy).
- Responde SIEMPRE en formato JSON válido con la estructura especificada.

Formato de respuesta JSON obligatorio:
{
    "thought": "Tu razonamiento sobre qué hacer",
    "action": "tool_use" o "respond",
    "tool_name": "nombre_herramienta" (si action es tool_use),
    "tool_args": { "arg": "value" } (si action es tool_use),
    "content": "Mensaje para el usuario si action es respond"
}
"""

            # Prompt de Usuario
            user_prompt = f"""
Contexto del proyecto:
{json.dumps(context.get('project_status', {}), indent=2, ensure_ascii=False)}

Tarea: {task}

Responde SOLO con el JSON de acción.
"""

            full_prompt = f"{system_prompt}\n\n{user_prompt}"

            # Llamada al LLM
            response = self.llm.invoke(full_prompt)
            content = response.content if hasattr(response, 'content') else str(response)

            self.tasks_completed += 1
            return {
                "content": content,
                "success": True
            }

        except Exception as e:
            self.tasks_failed += 1
            return {"error": str(e), "success": False}
        finally:
            self._update_status(AgentStatus.IDLE)