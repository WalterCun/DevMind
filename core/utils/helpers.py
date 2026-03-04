# devmind-core/core/utils/helpers.py
"""
Utilidades generales para DevMind Core.

Funciones helper para acceso seguro a atributos,
manejo de JSON, y operaciones comunes.
"""

import json
import re
from pathlib import Path
from typing import Any, Optional, TypeVar, Union, List, Dict

T = TypeVar('T')


def safe_get(obj: Optional[Any], attr: str, default: T = None) -> T:
    """
    Obtiene un atributo de forma segura.

    Args:
        obj: Objeto que puede ser None
        attr: Nombre del atributo a obtener
        default: Valor por defecto si no se puede obtener

    Returns:
        El valor del atributo o el default
    """
    if obj is None:
        return default
    return getattr(obj, attr, default)


def safe_chain(obj: Optional[Any], *attrs: str, default: Any = None) -> Any:
    """
    Obtiene una cadena de atributos de forma segura.

    Ejemplo:
        safe_chain(config, 'git_config', 'email', default='nobody@example.com')

    Args:
        obj: Objeto inicial que puede ser None
        *attrs: Nombres de atributos en cadena
        default: Valor por defecto si cualquier paso es None

    Returns:
        El valor final o el default
    """
    current = obj
    for attr in attrs:
        if current is None:
            return default
        current = getattr(current, attr, None)
        if current is None:
            return default
    return current if current is not None else default


def parse_json_safe(content: str, default: Any = None) -> Any:
    """
    Intenta parsear JSON de un string, con fallback seguro.

    Args:
        content: String que puede contener JSON
        default: Valor por defecto si el parseo falla

    Returns:
        Objeto parseado o default
    """
    if not content:
        return default

    try:
        # Intentar parsear directo
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Intentar extraer JSON de un bloque de texto
    # Busca el primer { y el último }
    match = re.search(r'\{.*\}', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Intentar con corchetes para arrays
    match = re.search(r'\[.*\]', content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return default


def truncate_text(text: str, max_length: int = 500, suffix: str = "...") -> str:
    """
    Trunca texto a una longitud máxima.

    Args:
        text: Texto a truncar
        max_length: Longitud máxima incluyendo el suffix
        suffix: Sufijo a agregar si se trunca

    Returns:
        Texto truncado
    """
    if len(text) <= max_length:
        return text

    # Reservar espacio para el suffix
    truncate_at = max_length - len(suffix)
    return text[:truncate_at].rstrip() + suffix


def format_file_size(bytes_: int) -> str:
    """
    Formatea tamaño de archivo en unidades legibles.

    Args:
        bytes_: Tamaño en bytes

    Returns:
        String formateado (ej: "2.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes_ < 1024.0:
            return f"{bytes_:.1f} {unit}"
        bytes_ /= 1024.0
    return f"{bytes_:.1f} PB"


def ensure_dir(path: Union[str, Path], create: bool = True) -> Path:
    """
    Asegura que un directorio existe.

    Args:
        path: Ruta del directorio
        create: Si True, crea el directorio si no existe

    Returns:
        Path object del directorio

    Raises:
        NotADirectoryError: Si el path existe pero no es directorio
        PermissionError: Si no hay permisos para crear
    """
    path_obj = Path(path)

    if create and not path_obj.exists():
        path_obj.mkdir(parents=True, exist_ok=True)

    if path_obj.exists() and not path_obj.is_dir():
        raise NotADirectoryError(f"{path} existe pero no es un directorio")

    return path_obj


def merge_dicts(base: Dict, override: Dict, deep: bool = True) -> Dict:
    """
    Fusiona dos diccionarios, con override teniendo prioridad.

    Args:
        base: Diccionario base
        override: Diccionario con valores a sobrescribir
        deep: Si True, fusiona recursivamente diccionarios anidados

    Returns:
        Nuevo diccionario fusionado
    """
    result = base.copy()

    for key, value in override.items():
        if (
                deep
                and key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
        ):
            result[key] = merge_dicts(result[key], value, deep=True)
        else:
            result[key] = value

    return result


def filter_dict(data: Dict, keys: Optional[List[str]] = None,
                exclude: Optional[List[str]] = None) -> Dict:
    """
    Filtra un diccionario por claves incluidas o excluidas.

    Args:
        data: Diccionario a filtrar
        keys: Lista de claves a incluir (None = todas)
        exclude: Lista de claves a excluir

    Returns:
        Diccionario filtrado
    """
    result = {}

    for key, value in data.items():
        if exclude and key in exclude:
            continue
        if keys and key not in keys:
            continue
        result[key] = value

    return result


def to_snake_case(text: str) -> str:
    """
    Convierte texto a snake_case.

    Args:
        text: Texto en cualquier formato

    Returns:
        Texto en snake_case
    """
    # Reemplazar espacios y guiones por underscores
    text = re.sub(r'[\s\-]+', '_', text)
    # Insertar underscore antes de mayúsculas
    text = re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', text)
    # Convertir a minúsculas y limpiar underscores múltiples
    return re.sub(r'_+', '_', text).lower().strip('_')


def to_camel_case(text: str, upper_first: bool = False) -> str:
    """
    Convierte texto a camelCase o PascalCase.

    Args:
        text: Texto en snake_case o cualquier formato
        upper_first: Si True, usa PascalCase; si False, camelCase

    Returns:
        Texto en camelCase o PascalCase
    """
    # Dividir por underscores, guiones o espacios
    parts = re.split(r'[_\-\s]+', text)
    # Capitalizar cada parte
    parts = [part.capitalize() for part in parts if part]

    if not parts:
        return ""

    if not upper_first and len(parts) > 1:
        parts[0] = parts[0].lower()

    return ''.join(parts)