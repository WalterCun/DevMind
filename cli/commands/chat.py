# devmind-core/cli/commands/chat.py
"""
Comando de chat de DevMind Core.

Inicia una sesión de conversación interactiva con el agente.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from core.config.manager import ConfigManager

console = Console()


@click.command('chat')
@click.argument('message', required=False)
@click.option('--project', '-p', 'project_id', help='ID del proyecto')
@click.option('--mode', '-m', type=click.Choice(['chat', 'plan', 'code', 'fix']), default='chat')
def chat_command(message: str, project_id: str, mode: str) -> None:
    """
    💬 Iniciar sesión de chat con el agente.

    Puedes enviar un mensaje inicial como argumento o entrar en modo interactivo.
    """
    config_manager = ConfigManager()

    # Verificar inicialización
    if not config_manager.is_initialized():
        console.print(Panel(
            "❌ Debes inicializar primero.\n\n"
            "Ejecuta: [bold]devmind init[/bold]",
            title="Configuración Requerida",
            style="red"
        ))
        return

    config = config_manager.get_config()

    console.print(Panel.fit(
        f"💬 Modo: [bold green]{mode.upper()}[/bold green]\n"
        f"🤖 Agente: [bold]{config.agent_name}[/bold]",
        style="green"
    ))
    console.print()

    # Si hay mensaje inicial, procesarlo
    if message:
        console.print(f"[bold blue]Tú:[/bold blue] {message}")
        # Aquí iría la lógica de procesamiento del mensaje
        console.print(f"[bold green]{config.agent_name}:[/bold green] Procesando...")
        console.print("(Implementación pendiente - Fase 1)")
        return

    # Modo interactivo
    console.print("Escribe tus mensajes. Usa [bold]/help[/bold] para comandos, [bold]/quit[/bold] para salir.\n")

    while True:
        try:
            user_input = click.prompt(click.style("Tú", fg="blue", bold=True), type=str)

            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print(f"\n👋 ¡Hasta luego! Soy {config.agent_name}, tu agente de desarrollo.")
                break

            if user_input.lower() == '/help':
                _show_help()
                continue

            # Aquí iría la lógica de procesamiento del mensaje
            console.print(f"[bold green]{config.agent_name}:[/bold green] Procesando...")
            console.print("(Implementación pendiente - Fase 1)\n")

        except KeyboardInterrupt:
            console.print("\n\n👋 Sesión terminada por el usuario.")
            break
        except EOFError:
            console.print("\n\n👋 Sesión terminada.")
            break


def _show_help() -> None:
    """Muestra ayuda de comandos"""
    help_text = """
## Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/help` | Mostrar esta ayuda |
| `/quit` | Salir del chat |
| `/status` | Ver estado del proyecto |
| `/plan` | Cambiar a modo planificación |
| `/code` | Cambiar a modo código |
| `/fix` | Cambiar a modo corrección |
| `/config` | Ver configuración actual |

## Consejos

- Sé específico en tus solicitudes
- Proporciona contexto cuando sea relevante
- Usa `/plan` para planificación de proyectos grandes
- Usa `/fix` para reportar bugs
"""
    console.print(Markdown(help_text))
    console.print()