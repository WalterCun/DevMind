# devmind-core/core/config/__init__.py
"""
Módulo de configuración de DevMind Core.

Gestiona la identidad, capacidades y preferencias del agente autónomo.
"""

from .manager import ConfigManager
from .schema import AgentConfig, PersonalityType, AutonomyMode, LearningMode, AuditFrequency
from .wizard import OnboardingWizard

__all__ = [
    "AgentConfig",
    "PersonalityType",
    "AutonomyMode",
    "LearningMode",
    "AuditFrequency",
    "ConfigManager",
    "OnboardingWizard",
]