# devmind-core/core/self_improvement/__init__.py
"""
Módulo de auto-mejora de DevMind Core.

Los imports son condicionales para permitir testing sin implementación completa.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tool_builder import ToolBuilderAgent
    from .agent_creator import AgentCreatorAgent
    from .language_learner import LanguageLearnerAgent
    from .capability_validator import CapabilityValidator, ValidationLevel

__all__ = []

# Imports condicionales para runtime
try:
    from .tool_builder import ToolBuilderAgent
    __all__.append("ToolBuilderAgent")
except ImportError:
    pass

try:
    from .agent_creator import AgentCreatorAgent
    __all__.append("AgentCreatorAgent")
except ImportError:
    pass

try:
    from .language_learner import LanguageLearnerAgent
    __all__.append("LanguageLearnerAgent")
except ImportError:
    pass

try:
    from .capability_validator import CapabilityValidator, ValidationLevel
    __all__.append("CapabilityValidator")
    __all__.append("ValidationLevel")
except ImportError:
    pass