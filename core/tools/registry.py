# devmind-core/core/tools/registry.py
"""
Registro central de herramientas para DevMind Core.

Permite registrar, buscar y ejecutar herramientas
de forma dinámica.
"""

import importlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseTool, ToolResult

logger = logging.getLogger(__name__)

from core.tools.builtin import BUILTIN_TOOLS


class ToolRegistry:
    """
    Registro singleton de herramientas.

    Características:
    - Registro dinámico de herramientas
    - Búsqueda por nombre, categoría o tags
    - Carga automática desde directorios
    - Estadísticas de uso
    """

    _instance: Optional['ToolRegistry'] = None
    _tools: Dict[str, BaseTool]
    _auto_generated_dir: Path

    # Dentro de core/tools/registry.py -> Clase ToolRegistry -> Método __new__
    def __new__(cls) -> 'ToolRegistry':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._tools = {}
            cls._instance._auto_generated_dir = Path.home() / ".devmind" / "tools" / "auto_generated"
            cls._instance._auto_generated_dir.mkdir(parents=True, exist_ok=True)

            try:
                from core.tools.builtin import BUILTIN_TOOLS
                for tool_class in BUILTIN_TOOLS:
                    try:
                        instance = tool_class()
                        cls._instance.register(instance)
                        logger.debug(f"Auto-loaded builtin tool: {instance.definition.name}")
                    except Exception as e:
                        logger.error(f"Failed to load builtin tool {tool_class.__name__}: {e}")
            except ImportError:
                logger.warning("Could not import builtin tools.")

        return cls._instance

    def register(self, tool: BaseTool) -> str:
        """Registra una herramienta"""
        name = tool.definition.name

        if name in self._tools:
            logger.warning(f"Tool '{name}' already registered, overwriting")

        self._tools[name] = tool
        logger.info(f"Registered tool: {name} ({tool.definition.category})")
        return name

    def unregister(self, name: str) -> bool:
        """Elimina una herramienta del registro"""
        if name in self._tools:
            del self._tools[name]
            logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[BaseTool]:
        """Obtiene una herramienta por nombre"""
        return self._tools.get(name)

    def execute(self, name: str, **kwargs) -> ToolResult:
        """Ejecuta una herramienta por nombre"""
        tool = self.get(name)

        if not tool:
            return ToolResult(
                success=False,
                output=None,
                error=f"Tool '{name}' not found"
            )

        try:
            # Validar parámetros
            validated = tool.validate_parameters(**kwargs)

            # Ejecutar
            import time
            start = time.time()
            result = tool.execute(**validated)
            result.execution_time = time.time() - start

            # Registrar ejecución
            tool._record_execution(datetime.now(), result.success)

            return result

        except Exception as e:
            logger.error(f"Tool execution error ({name}): {e}")
            return ToolResult(
                success=False,
                output=None,
                error=str(e)
            )

    def list_tools(
            self,
            category: Optional[str] = None,
            tag: Optional[str] = None,
            author: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Lista herramientas con filtros opcionales"""
        tools = []

        for tool in self._tools.values():
            # Aplicar filtros
            if category and tool.definition.category != category:
                continue
            if tag and tag not in tool.definition.tags:
                continue
            if author and tool.definition.author != author:
                continue

            tools.append(tool.to_dict())

        return tools

    def search(self, query: str) -> List[Dict[str, Any]]:
        """Busca herramientas por texto"""
        query_lower = query.lower()
        results = []

        for tool in self._tools.values():
            # Buscar en nombre, descripción y tags
            searchable = f"{tool.definition.name} {tool.definition.description} {' '.join(tool.definition.tags)}".lower()

            if query_lower in searchable:
                results.append(tool.to_dict())

        return results

    def get_categories(self) -> List[str]:
        """Obtiene todas las categorías disponibles"""
        return list(set(t.definition.category for t in self._tools.values()))

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del registro"""
        total_executions = sum(t.execution_count for t in self._tools.values())

        return {
            "total_tools": len(self._tools),
            "by_category": self._count_by_category(),
            "by_author": self._count_by_author(),
            "total_executions": total_executions,
            "auto_generated": len(list(self._auto_generated_dir.glob("*.py")))
        }

    def _count_by_category(self) -> Dict[str, int]:
        """Cuenta herramientas por categoría"""
        counts = {}
        for tool in self._tools.values():
            cat = tool.definition.category
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def _count_by_author(self) -> Dict[str, int]:
        """Cuenta herramientas por autor"""
        counts = {}
        for tool in self._tools.values():
            author = tool.definition.author
            counts[author] = counts.get(author, 0) + 1
        return counts

    def load_from_directory(self, directory: Path) -> int:
        """Carga herramientas desde un directorio"""
        if not directory.exists():
            return 0

        loaded = 0
        for file_path in directory.glob("*.py"):
            if file_path.name.startswith("_"):
                continue

            try:
                # Importar módulo dinámicamente
                spec = importlib.util.spec_from_file_location(
                    file_path.stem, file_path
                )
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                # Buscar clases que hereden de BaseTool
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (
                            isinstance(attr, type) and
                            issubclass(attr, BaseTool) and
                            attr != BaseTool
                    ):
                        tool = attr()
                        self.register(tool)
                        loaded += 1
                        logger.info(f"Loaded tool from {file_path}: {attr_name}")

            except Exception as e:
                logger.error(f"Failed to load tool from {file_path}: {e}")

        return loaded

    def save_tool_to_file(self, tool: BaseTool, file_path: Path) -> bool:
        """Guarda una herramienta a un archivo Python"""
        try:
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Generar código Python de la herramienta
            code = self._generate_tool_code(tool)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(code)

            logger.info(f"Saved tool to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to save tool: {e}")
            return False

    def _generate_tool_code(self, tool: BaseTool) -> str:
        """Genera código Python para una herramienta"""
        # Implementación simplificada - en producción sería más robusta
        return f'''# Tool: {tool.definition.name}
# Auto-generated by DevMind Core

from core.tools.base import BaseTool, ToolDefinition, ToolResult, ToolParameter
from datetime import datetime

class {tool.definition.name.replace(" ", "")}Tool(BaseTool):
    """{tool.definition.description}"""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="{tool.definition.name}",
            description="{tool.definition.description}",
            category="{tool.definition.category}",
            tags={tool.definition.tags},
            author="ai-generated",
            version="{tool.definition.version}"
        )

    def execute(self, **kwargs) -> ToolResult:
        # TODO: Implementar lógica de la herramienta
        return ToolResult(
            success=True,
            output="Tool executed successfully"
        )
'''

    def reset(self) -> None:
        """Resetea el registro (útil para testing)"""
        self._tools.clear()