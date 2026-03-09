# core/tools/builtin/file_ops.py
"""
Herramientas para manipulación segura de archivos del proyecto.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any

from core.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult

logger = logging.getLogger(__name__)


class WriteFileTool(BaseTool):
    """Herramienta para escribir/crear archivos en el proyecto."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="write_file",
            description="Escribe o sobrescribe contenido en un archivo dentro del proyecto. Crea directorios padres si no existen.",
            category="file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="str",
                    description="Ruta relativa del archivo desde la raíz del proyecto (ej: 'app/models.py')",
                    required=True
                ),
                ToolParameter(
                    name="content",
                    type="str",
                    description="Contenido completo a escribir en el archivo",
                    required=True
                )
            ],
            tags=["file", "write", "create"]
        )

    def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")
        content = kwargs.get("content")

        if not file_path or content is None:
            return ToolResult(success=False, error="Parámetros 'file_path' y 'content' son requeridos")

        try:
            # Determinar la raíz del proyecto
            project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
            full_path = project_root / file_path

            # Seguridad: Asegurar que no salimos del directorio del proyecto
            try:
                full_path.resolve().relative_to(project_root.resolve())
            except ValueError:
                return ToolResult(success=False,
                                  error="Acceso denegado: Intento de escribir fuera del directorio del proyecto")

            # Crear directorios si no existen
            full_path.parent.mkdir(parents=True, exist_ok=True)

            # Escribir archivo
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)

            logger.info(f"Archivo escrito exitosamente: {full_path}")
            return ToolResult(
                success=True,
                output=f"Archivo creado/actualizado: {file_path}",
                metadata={"path": str(full_path), "size": len(content)}
            )

        except PermissionError:
            logger.error(f"Permiso denegado al escribir {file_path}")
            return ToolResult(success=False, error=f"Permiso denegado al escribir en {file_path}")
        except Exception as e:
            logger.error(f"Error escribiendo archivo: {e}")
            return ToolResult(success=False, error=str(e))


class ReadFileTool(BaseTool):
    """Herramienta para leer archivos existentes del proyecto."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="read_file",
            description="Lee el contenido de un archivo existente en el proyecto.",
            category="file",
            parameters=[
                ToolParameter(
                    name="file_path",
                    type="str",
                    description="Ruta relativa del archivo a leer",
                    required=True
                )
            ],
            tags=["file", "read"]
        )

    def execute(self, **kwargs) -> ToolResult:
        file_path = kwargs.get("file_path")

        if not file_path:
            return ToolResult(success=False, error="Parámetro 'file_path' es requerido")

        try:
            project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
            full_path = project_root / file_path

            if not full_path.exists():
                return ToolResult(success=False, error=f"Archivo no encontrado: {file_path}")

            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()

            return ToolResult(
                success=True,
                output=content,
                metadata={"path": str(full_path), "size": len(content)}
            )

        except Exception as e:
            logger.error(f"Error leyendo archivo: {e}")
            return ToolResult(success=False, error=str(e))


class ListFilesTool(BaseTool):
    """Herramienta para listar archivos en un directorio."""

    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="list_files",
            description="Lista archivos y directorios en una ruta dada.",
            category="file",
            parameters=[
                ToolParameter(
                    name="directory_path",
                    type="str",
                    description="Directorio relativo a listar (por defecto raíz)",
                    required=False,
                    default="."
                )
            ]
        )

    def execute(self, **kwargs) -> ToolResult:
        dir_path = kwargs.get("directory_path", ".")
        try:
            project_root = Path(os.getenv("PROJECT_ROOT", os.getcwd()))
            full_path = project_root / dir_path

            if not full_path.exists():
                return ToolResult(success=False, error=f"Directorio no encontrado: {dir_path}")

            items = []
            for item in full_path.iterdir():
                # Ignorar carpetas ocultas y __pycache__
                if item.name.startswith('.') or item.name == '__pycache__':
                    continue
                item_type = "DIR" if item.is_dir() else "FILE"
                items.append(f"[{item_type}] {item.name}")

            return ToolResult(
                success=True,
                output="\n".join(items),
                metadata={"count": len(items)}
            )
        except Exception as e:
            return ToolResult(success=False, error=str(e))


__all__ = ['WriteFileTool', 'ReadFileTool', 'ListFilesTool']