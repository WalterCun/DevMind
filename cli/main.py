# devmind-core/cli/main.py
"""
Entry point principal de DevMind Core CLI.

Punto de entrada para todos los comandos de la interfaz de línea de comandos.
"""
import logging
import os
from pathlib import Path

import click
from dotenv import load_dotenv
from rich.console import Console

from cli.commands import tools_group, addons_group
from cli.commands.chat import chat_command
from cli.commands.code import code_command
from cli.commands.config import config_command
from cli.commands.doctor import doctor_command
from cli.commands.fix import fix_command
from cli.commands.init import init_command
from cli.commands.plan import plan_command
from cli.commands.status import status_command
from core.utils.logger import setup_logging

env_path = Path(__file__).parent.parent / '.env'

if env_path.exists():
    load_dotenv(env_path)

is_production = bool(os.getenv("DEVMIND_PRODUCTION", "False"))
log_level = os.getenv("LOG_LEVEL", "WARNING" if is_production else "DEBUG")
console_output = bool(os.getenv("LOG_CONSOLE", f"{is_production}"))

setup_logging(
    level=log_level,
    log_file=os.getenv("LOG_FILE", "~/.devmind/devmind.log"),
    console_output=console_output
)

logger = logging.getLogger(__name__)

console = Console()


@click.group()
@click.version_option(version="0.6.0", prog_name="devmind")
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
@click.option('--production', '-p', is_flag=True, help='Modo producción')
def main(verbose: bool, production: bool) -> None:
    """
    🤖 DevMind Core - Tu ingeniero de software autónomo

    Una plataforma de desarrollo auto-alojada que actúa como un equipo
    de ingeniería completo. Planifica, codifica, depura y se auto-mejora.

    \b
    Comandos principales:
      init          Configurar agente por primera vez
      chat          Conversación interactiva con el agente
      plan          Planificar proyecto en fases
      code          Generar código con IA
      fix           Auto-fix de bugs
      status        Ver estado del sistema
      config        Modificar configuración
      doctor        Diagnóstico completo

    Ejemplos:

        devmind init
        devmind chat "Quiero crear una API para hoteles"
        devmind plan --project hotel-api "API REST con Django"
        devmind code -p hotel-api "Modelo Reservation con campos..."
        devmind fix -p hotel-api "Error 500 al filtrar por fecha"
        devmind doctor
    """
    if verbose:
        os.environ['LOG_LEVEL'] = 'DEBUG'
        os.environ['LOG_CONSOLE'] = 'True'

    if production:
        os.environ['LOG_LEVEL'] = 'WARNING'
        os.environ['LOG_CONSOLE'] = 'False'


# Registrar todos los comandos
main.add_command(init_command)
main.add_command(chat_command)
main.add_command(status_command)
main.add_command(config_command)
main.add_command(doctor_command)
main.add_command(plan_command)
main.add_command(code_command)
main.add_command(fix_command)
main.add_command(tools_group)
main.add_command(addons_group)

if __name__ == '__main__':
    main()
