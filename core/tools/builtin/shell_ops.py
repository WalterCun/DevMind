# core/tools/builtin/shell_ops.py
"""
Herramientas para ejecución de comandos de shell.
"""
import subprocess
import os
import logging
from typing import Dict, Any

from core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class RunCommandTool(BaseTool):
    """Ejecuta comandos de shell en el entorno del proyecto."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="run_command",
            description=(
                "Ejecuta un comando de shell. Útil para instalar dependencias "
                "(pip install, npm install), correr tests (pytest, npm test) "
                "o ejecutar scripts. Usa con precaución."
            ),
            category="system",
            parameters=[
                ToolParameter(
                    name="command",
                    type="str",
                    description="Comando a ejecutar (ej: 'pytest tests/')",
                    required=True
                ),
                ToolParameter(
                    name="timeout",
                    type="int",
                    description="Timeout en segundos (default 60)",
                    required=False,
                    default=60
                )
            ],
            tags=["shell", "execute", "process"]
        )

    def execute(self, **kwargs) -> ToolResult:
        command = kwargs.get("command")
        timeout = kwargs.get("timeout", 60)

        if not command:
            return ToolResult(success=False, error="Comando no especificado")

        cwd = os.getenv("PROJECT_ROOT", os.getcwd())

        try:
            logger.warning(f"Ejecutando comando shell: {command}")

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=cwd
            )

            output = result.stdout.strip()
            error_output = result.stderr.strip()

            full_output = f"EXIT CODE: {result.returncode}\n"
            if output:
                full_output += f"STDOUT:\n{output}\n"
            if error_output:
                full_output += f"STDERR:\n{error_output}\n"

            return ToolResult(
                success=(result.returncode == 0),
                output=full_output,
                metadata={
                    "exit_code": result.returncode,
                    "command": command
                }
            )

        except subprocess.TimeoutExpired:
            logger.error(f"Timeout ejecutando comando: {command}")
            return ToolResult(success=False, error=f"Comando excedió timeout de {timeout}s")
        except Exception as e:
            logger.error(f"Error ejecutando comando: {e}")
            return ToolResult(success=False, error=str(e))


__all__ = ['RunCommandTool']