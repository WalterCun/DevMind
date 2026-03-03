# devmind-core/cli/main.py
"""
Entry point principal de DevMind Core CLI.

Punto de entrada para todos los comandos de la interfaz de línea de comandos.
"""

import click
from rich.console import Console
from rich.panel import Panel

from cli.commands.doctor import doctor_command
from cli.commands.init import init_command
from cli.commands.chat import chat_command
from cli.commands.status import status_command
from cli.commands.config import config_command

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="devmind")
@click.option('--verbose', '-v', is_flag=True, help='Modo verbose')
def main(verbose: bool) -> None:
    """
    🤖 DevMind Core - Tu ingeniero de software autónomo

    Una plataforma de desarrollo auto-alojada que actúa como un equipo
    de ingeniería completo. Planifica, codifica, depura y se auto-mejora.

    Ejemplos:

        devmind init              # Configurar por primera vez
        devmind chat              # Iniciar conversación
        devmind status            # Ver estado del sistema
        devmind config --show     # Ver configuración completa
    """
    if verbose:
        import os
        os.environ['LOG_LEVEL'] = 'DEBUG'


# Registrar comandos
main.add_command(init_command)
main.add_command(chat_command)
main.add_command(status_command)
main.add_command(config_command)
main.add_command(doctor_command)

if __name__ == '__main__':
    main()