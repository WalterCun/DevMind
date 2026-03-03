# devmind-core/core/tools/base.py
"""
Clase base para herramientas de DevMind Core.

Las herramientas son funciones o capacidades que los agentes
pueden usar para interactuar con el mundo exterior.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class ToolParameter:
    """Parámetro de una herramienta"""
    name: str
    type: str  # str, int, float, bool, list, dict
    description: str
    required: bool = True
    default: Any = None
    enum: Optional[List[Any]] = None


@dataclass
class ToolResult:
    """Resultado de la ejecución de una herramienta"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "output": self.output,
            "error": self.error,
            "execution_time": round(self.execution_time, 3),
            "metadata": self.metadata  # ← Ahora sí existe
        }


@dataclass
class ToolDefinition:
    """Definición de una herramienta"""
    name: str
    description: str
    category: str  # file, code, web, system, custom
    parameters: List[ToolParameter] = field(default_factory=list)
    returns: str = "any"
    examples: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    author: str = "system"  # system, user, ai-generated
    version: str = "1.0.0"


class BaseTool(ABC):
    """
    Clase base abstracta para todas las herramientas.

    Las herramientas deben implementar:
    - name: Nombre único de la herramienta
    - description: Descripción de lo que hace
    - parameters: Lista de parámetros que acepta
    - execute(): Método principal de ejecución
    """

    def __init__(self):
        self.execution_count = 0
        self.last_execution: Optional[datetime] = None
        self.total_execution_time = 0.0

    @property
    @abstractmethod
    def definition(self) -> ToolDefinition:
        """Retorna la definición de la herramienta"""
        pass

    @abstractmethod
    def execute(self, **kwargs) -> ToolResult:
        """
        Ejecuta la herramienta con los parámetros dados.

        Args:
            **kwargs: Parámetros de la herramienta

        Returns:
            ToolResult con el resultado de la ejecución
        """
        pass

    def validate_parameters(self, **kwargs) -> Dict[str, Any]:
        """Valida los parámetros contra la definición"""
        validated = {}
        errors = []

        for param in self.definition.parameters:
            value = kwargs.get(param.name, param.default)

            # Verificar requeridos
            if param.required and value is None:
                errors.append(f"Parámetro requerido faltante: {param.name}")
                continue

            if value is None:
                continue

            # Verificar tipo
            if not self._check_type(value, param.type):
                errors.append(f"Tipo inválido para {param.name}: esperado {param.type}")
                continue

            # Verificar enum
            if param.enum and value not in param.enum:
                errors.append(f"Valor inválido para {param.name}: debe ser uno de {param.enum}")
                continue

            validated[param.name] = value

        if errors:
            raise ValueError("; ".join(errors))

        return validated

    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Verifica si un valor coincide con el tipo esperado"""
        type_map = {
            "str": str,
            "int": int,
            "float": (int, float),
            "bool": bool,
            "list": list,
            "dict": dict,
            "any": object
        }

        expected = type_map.get(expected_type, object)
        return isinstance(value, expected)

    def _record_execution(self, start_time: datetime, success: bool) -> None:
        """Registra estadísticas de ejecución"""
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()

        self.execution_count += 1
        self.last_execution = end_time
        self.total_execution_time += execution_time

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas de uso de la herramienta"""
        return {
            "name": self.definition.name,
            "execution_count": self.execution_count,
            "last_execution": self.last_execution.isoformat() if self.last_execution else None,
            "total_execution_time": round(self.total_execution_time, 3),
            "avg_execution_time": round(
                self.total_execution_time / max(1, self.execution_count), 3
            )
        }

    def to_dict(self) -> Dict[str, Any]:
        """Serializa la herramienta a dict"""
        return {
            "definition": {
                "name": self.definition.name,
                "description": self.definition.description,
                "category": self.definition.category,
                "parameters": [
                    {
                        "name": p.name,
                        "type": p.type,
                        "description": p.description,
                        "required": p.required,
                        "default": p.default
                    }
                    for p in self.definition.parameters
                ],
                "returns": self.definition.returns,
                "examples": self.definition.examples,
                "tags": self.definition.tags,
                "author": self.definition.author,
                "version": self.definition.version
            },
            "stats": self.get_stats()
        }
