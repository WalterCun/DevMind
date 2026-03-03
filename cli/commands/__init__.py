# devmind-core/cli/commands/__init__.py
"""
Comandos CLI de DevMind Core.

Módulo que exporta todos los comandos disponibles en la CLI.
"""
from .code import code_command
from .doctor import doctor_command
from .fix import fix_command
from .init import init_command
from .chat import chat_command
from .plan import plan_command
from .status import status_command
from .config import config_command

__all__ = [
    "init_command",
    "chat_command",
    "status_command",
    "config_command",
    "doctor_command",
    "plan_command",
    "code_command",
    "fix_command",
]