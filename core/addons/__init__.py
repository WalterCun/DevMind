# devmind-core/core/addons/__init__.py
"""
Sistema de addons de DevMind Core.
"""

from .base import BaseAddon, AddonManifest
from .registry import AddonRegistry
from .loader import AddonLoader

__all__ = [
    "BaseAddon",
    "AddonManifest",
    "AddonRegistry",
    "AddonLoader",
]