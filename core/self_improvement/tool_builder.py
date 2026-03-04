# devmind-core/core/self_improvement/tool_builder.py
"""
ToolBuilder Agent - Crea herramientas automáticamente.

Este agente analiza necesidades del sistema y genera
nuevas herramientas para satisfacerlas.
"""

import json
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional

from ..agents.base import BaseAgent, AgentLevel, AgentStatus
from ..memory.vector_store import VectorMemory
from ..security.validator import CodeValidator
from ..tools.base import BaseTool
from ..tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolBuilderAgent(BaseAgent):
    """
    Agente especializado en crear nuevas herramientas.

    Características:
    - Analiza descripciones de necesidades
    - Genera código de herramientas
    - Valida herramientas antes de registrar
    - Aprende de herramientas existentes
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Tool Builder",
            role="Creador de Herramientas Autónomo",
            goal="Crear, validar y registrar nuevas herramientas para expandir capacidades del sistema",
            backstory="""Eres un ingeniero de herramientas especializado en crear utilidades
            que resuelven problemas específicos. Tu código es modular, testeable y bien documentado.
            Siempre validas la seguridad del código antes de registrarlo.""",
            level=AgentLevel.EXECUTION,
            **kwargs
        )

        self.tool_registry = ToolRegistry()
        self.tools_created = 0
        self.tools_validated = 0
        self.memory: Optional[VectorMemory] = None

    def set_memory(self, memory: VectorMemory) -> None:
        """Establece la memoria vectorial para consultar herramientas existentes"""
        self.memory = memory

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea una nueva herramienta basada en la descripción.

        Flujo:
        1. Analizar necesidad
        2. Diseñar herramienta
        3. Generar código
        4. Validar herramienta
        5. Registrar herramienta

        Args:
            task: Descripción de la herramienta a crear
            context: Contexto adicional (proyecto, lenguajes, etc.)

        Returns:
            Dict con resultado de la creación
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Paso 1: Analizar necesidad
            analysis = self._analyze_need(task, context)
            logger.info(f"Análisis completado: {analysis.get('name', 'unknown')}")

            # Paso 2: Diseñar herramienta
            design = self._design_tool(analysis)
            logger.info(f"Diseño completado: {design.get('name', 'unknown')}")

            # Paso 3: Generar código
            implementation = self._generate_code(design)
            logger.info(f"Código generado: {implementation.get('file_path')}")

            # Paso 4: Validar herramienta
            validation = self._validate_tool(implementation)

            if validation.get("valid"):
                # Paso 5: Registrar herramienta
                registration = self._register_tool(implementation)

                self.tools_created += 1

                # Almacenar en memoria si está disponible
                if self.memory:
                    self._store_tool_knowledge(design, implementation)

                return {
                    "success": True,
                    "tool_name": design.get("name"),
                    "file_path": implementation.get("file_path"),
                    "registration": registration,
                    "validation": validation,
                    "message": f"Herramienta '{design.get('name')}' creada y registrada exitosamente"
                }
            else:
                self.tools_validated -= 1  # Contabilizar fallo
                return {
                    "success": False,
                    "error": "La herramienta no pasó validación",
                    "validation_errors": validation.get("errors", [])
                }

        except Exception as e:
            logger.error(f"ToolBuilder error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "traceback": logger.exception("Detailed error")
            }
        finally:
            self._update_status(AgentStatus.IDLE)

    def _analyze_need(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Analiza la necesidad para determinar qué herramienta crear"""
        # Consultar herramientas existentes para evitar duplicados
        existing_tools = []
        if self.memory:
            existing = self.memory.retrieve(
                query=task,
                categories=["tools"],
                limit=5
            )
            existing_tools = [e["content"][:200] for e in existing]

        prompt = f"""
        Analiza esta necesidad de herramienta:

        TAREA: {task}
        CONTEXTO: {json.dumps(context, indent=2)}

        Herramientas existentes similares:
        {json.dumps(existing_tools, indent=2)}

        Proporciona un análisis estructurado con:
        1. name: Nombre sugerido para la herramienta (PascalCase, único)
        2. description: Descripción de funcionalidad principal (1-2 frases)
        3. parameters: Lista de objetos con {{name, type, description, required, default}}
        4. returns: Tipo de dato esperado de retorno
        5. category: Una de [file, code, web, system, custom]
        6. dependencies: Lista de paquetes Python externos necesarios
        7. use_cases: Lista de 3 casos de uso principales
        8. error_handling: Posibles errores a manejar y cómo

        Responde SOLO en formato JSON válido, sin texto adicional.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _design_tool(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña la arquitectura de la herramienta"""
        prompt = f"""
        Diseña la herramienta basada en este análisis:

        {json.dumps(analysis, indent=2)}

        Proporciona:
        1. class_name: Nombre de clase (formato: {analysis.get('name', 'Tool')}Tool)
        2. parameters: Lista completa de ToolParameter dicts
        3. execute_logic: Pseudocódigo paso a paso del método execute()
        4. error_handling: Estrategia específica para cada error posible
        5. examples: 3 ejemplos de uso con código Python
        6. tags: Lista de 5-10 tags para búsqueda
        7. docstring: Docstring completo para la clase

        Responde SOLO en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _generate_code(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Genera el código de la herramienta"""
        prompt = f"""
        Implementa esta herramienta en Python siguiendo EXACTAMENTE estos requisitos:

        DISEÑO:
        {json.dumps(design, indent=2)}

        REQUISITOS OBLIGATORIOS:
        1. Heredar de core.tools.base.BaseTool
        2. Implementar @property definition que retorne ToolDefinition
        3. Implementar execute(self, **kwargs) -> ToolResult
        4. Incluir type hints completos en todos los métodos
        5. Docstrings en formato Google style para clase y métodos
        6. Manejo de errores con logging apropiado
        7. Validación de parámetros con validate_parameters()
        8. No usar eval(), exec(), os.system(), subprocess con shell=True
        9. Incluir tests unitarios básicos al final del archivo en bloque if __name__ == "__main__"
        10. Seguir PEP 8 para formato de código

        Proporciona SOLO el código Python completo, sin explicaciones ni markdown.
        """

        response = self.llm.invoke(prompt)
        code = response.content

        # Limpiar código de posibles bloques markdown
        code = re.sub(r'^```python\s*', '', code)
        code = re.sub(r'\s*```$', '', code)
        code = code.strip()

        # Guardar archivo
        tool_name = design.get("class_name", "CustomTool").replace(" ", "")
        file_path = self.tool_registry._auto_generated_dir / f"{tool_name.lower()}.py"
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code)

        return {
            "code": code,
            "file_path": str(file_path),
            "tool_name": tool_name,
            "class_name": design.get("class_name")
        }

    def _validate_tool(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Valida que la herramienta generada es funcional y segura"""
        code = implementation["code"]
        errors = []

        # 1. Validación de seguridad del código
        validator = CodeValidator(language="python")
        validation_result = validator.validate(code)

        if not validation_result.valid:
            errors.extend([
                f"{f.rule_name}: {f.message}"
                for f in validation_result.findings
                if f.severity.name in ["HIGH", "CRITICAL"]
            ])

        # 2. Validación de estructura
        structure_checks = [
            ("BaseTool", "La herramienta debe heredar de BaseTool"),
            ("ToolDefinition", "Debe tener ToolDefinition"),
            ("def execute", "Debe implementar método execute()"),
            ("-> ToolResult", "execute() debe retornar ToolResult"),
            ("from core.tools.base", "Debe importar de core.tools.base"),
        ]

        for check, message in structure_checks:
            if check not in code:
                errors.append(message)

        # 3. Validación de documentación
        if '"""' not in code and "'''" not in code:
            errors.append("Falta docstring en la clase")

        if "->" not in code or ": " not in code:
            errors.append("Faltan type hints en los métodos")

        # 4. Intentar importar y ejecutar tests básicos
        if not errors:
            try:
                import importlib.util
                import sys

                # Cargar módulo dinámicamente
                spec = importlib.util.spec_from_file_location(
                    "test_tool", implementation["file_path"]
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    sys.modules["test_tool"] = module
                    spec.loader.exec_module(module)

                    # Buscar la clase de herramienta
                    tool_class = None
                    class_name = implementation.get("class_name")

                    if class_name and hasattr(module, class_name):
                        tool_class = getattr(module, class_name)
                    else:
                        # Buscar cualquier clase que herede de BaseTool
                        for attr_name in dir(module):
                            attr = getattr(module, attr_name)
                            if (isinstance(attr, type) and
                                    issubclass(attr, BaseTool) and
                                    attr != BaseTool):
                                tool_class = attr
                                break

                    if not tool_class:
                        errors.append("No se encontró clase que herede de BaseTool")
                    else:
                        # Instanciar y verificar definición
                        tool = tool_class()
                        if not hasattr(tool, 'definition') or not tool.definition:
                            errors.append("La herramienta no tiene propiedad definition")
                        elif not tool.definition.name:
                            errors.append("ToolDefinition no tiene nombre")
                        else:
                            self.tools_validated += 1

            except Exception as e:
                errors.append(f"Error validando herramienta: {type(e).__name__}: {str(e)}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "security_findings": [f.to_dict() for f in
                                  validation_result.findings] if not validation_result.valid else []
        }

    def _register_tool(self, implementation: Dict[str, Any]) -> Dict[str, Any]:
        """Registra la herramienta en el registry"""
        try:
            # Recargar desde archivo
            loaded = self.tool_registry.load_from_directory(
                Path(implementation["file_path"]).parent
            )

            # Verificar que se registró
            tool_name = implementation.get("tool_name")
            tool = self.tool_registry.get(tool_name)

            if tool:
                return {
                    "registered": True,
                    "tool_name": tool.definition.name,
                    "category": tool.definition.category,
                    "author": tool.definition.author
                }
            else:
                # Intentar registro manual
                import importlib.util
                spec = importlib.util.spec_from_file_location(
                    tool_name, implementation["file_path"]
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if isinstance(attr, type) and issubclass(attr, BaseTool) and attr != BaseTool:
                            tool = attr()
                            self.tool_registry.register(tool)
                            return {
                                "registered": True,
                                "tool_name": tool.definition.name,
                                "category": tool.definition.category
                            }

                return {
                    "registered": False,
                    "error": "Herramienta no se pudo registrar automáticamente"
                }

        except Exception as e:
            return {
                "registered": False,
                "error": str(e)
            }

    def _store_tool_knowledge(self, design: Dict[str, Any], implementation: Dict[str, Any]) -> None:
        """Almacena conocimiento sobre la herramienta en memoria"""
        if not self.memory:
            return

        knowledge = f"""
        Herramienta: {design.get('class_name')}
        Categoría: {design.get('category')}
        Descripción: {design.get('description')}

        Parámetros:
        {json.dumps(design.get('parameters', []), indent=2)}

        Ejemplos de uso:
        {json.dumps(design.get('examples', []), indent=2)}
        """

        self.memory.store(
            content=knowledge,
            metadata={
                "tool_name": design.get("class_name"),
                "category": design.get("category"),
                "file_path": implementation.get("file_path")
            },
            category="tools"
        )

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM de forma robusta"""
        # Intentar extraer JSON de diferentes formatos
        patterns = [
            r'\{.*\}',  # JSON simple
            r'```json\s*(.*?)\s*```',  # JSON en bloque markdown
            r'```.*?\n(.*?)\n```',  # Cualquier bloque de código
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if len(match.groups()) > 0 else match.group())
                except json.JSONDecodeError:
                    continue

        # Fallback: intentar parsear todo el contenido
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Último recurso: retornar contenido raw
        return {"raw": content, "content": content}

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del ToolBuilder"""
        return {
            "tools_created": self.tools_created,
            "tools_validated": self.tools_validated,
            "success_rate": round(
                self.tools_validated / max(1, self.tools_created) * 100, 1
            ) if self.tools_created > 0 else 0.0,
            "memory_available": self.memory is not None
        }