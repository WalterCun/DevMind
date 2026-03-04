# devmind-core/core/addons/__init__.py
"""
Sistema de addons de DevMind Core.
"""

from .base import BaseAddon, AddonManifest
from .loader import AddonLoader
from .registry import AddonRegistry

__all__ = [
    "BaseAddon",
    "AddonManifest",
    "AddonRegistry",
    "AddonLoader",
]