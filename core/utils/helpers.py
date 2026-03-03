# devmind-core/core/utils/helpers.py
"""
Utilidades generales para DevMind Core.
"""

from typing import Any, Optional, TypeVar

T = TypeVar('T')


def safe_get(obj: Optional[Any], attr: str, default: T = None) -> T:
    """
    Obtiene un atributo de forma segura, retornando default si obj es None
    o el atributo no existe.

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
        # Equivale a: config?.git_config?.email ?? 'nobody@example.com'

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