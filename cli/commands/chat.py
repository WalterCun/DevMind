# devmind-core/cli/commands/chat.py
"""
Comando chat para DevMind Core.
Proporciona interfaz interactiva de conversación con el agente.
"""

import asyncio

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator

console = Console()


@click.command('chat')
@click.option('--project', '-p', 'project_id', help='ID del proyecto')
@click.option('--clear', '-c', is_flag=True, help='Limpiar contexto e iniciar nuevo')
@click.option('--stream', '-s', is_flag=True, help='Streaming de respuesta token por token')
@click.argument('initial_message', nargs=1, required=False)  # ✅ Aceptar mensaje inicial opcional
def chat_command(project_id: str, clear: bool, stream: bool, initial_message: str):
    """💬 Conversación interactiva con el agente

    Ejemplos:
      devmind chat                          # Modo interactivo
      devmind chat "Hola"                   # Mensaje inicial
      devmind chat -p myproject "Planificar API"
    """

    # Cargar configuración
    config = ConfigManager().get_config()
    if not config:
        console.print(Panel(
            "[yellow]⚠️ Configuración no inicializada[/yellow]\n"
            "Ejecutá [bold]devmind init[/bold] primero",
            style="yellow"
        ))
        return

    # Inicializar orquestador
    orchestrator = DevMindOrchestrator(
        project_id=project_id,
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando el orchestrator[/red]")
        return

    # Mostrar banner
    console.print(Panel.fit(
        f"[bold]💬 Modo:[/bold] CHAT\n"
        f"[bold]🤖 Agente:[/bold] {config.agent_name}\n"
        f"[bold]⚡ Autonomía:[/bold] {config.autonomy_mode.value}",
        title="DevMind Chat",
        style="cyan"
    ))
    console.print()

    # Bucle principal de chat
    session_id = None

    # Si hay mensaje inicial, procesarlo primero
    if initial_message:
        console.print(f"[bold green]Tú[/bold green]: {initial_message}")
        console.print()
        console.print("[bold blue]Jarvis[/bold blue] está pensando...")

        result = asyncio.run(
            orchestrator.process_message(
                message=initial_message,
                session_id=session_id
            )
        )

        _display_response(result, stream)

        if result.get("session_id"):
            session_id = result["session_id"]

        console.print()

    # Modo interactivo: leer mensajes del usuario
    while True:
        try:
            # Obtener mensaje del usuario
            user_input = Prompt.ask("[bold green]Tú[/bold green]")

            # Comandos especiales
            if user_input.lower() in ['/quit', '/exit', '/q']:
                console.print("[dim]👋 Hasta luego[/dim]")
                break

            if user_input.lower() in ['/help', '/h']:
                _show_help()
                continue

            if user_input.lower() in ['/clear', '/cls'] or clear:
                console.print("[dim]🧹 Contexto limpiado[/dim]")
                session_id = None
                continue

            # Procesar mensaje
            console.print()
            console.print("[bold blue]Jarvis[/bold blue] está pensando...")

            result = asyncio.run(
                orchestrator.process_message(
                    message=user_input,
                    session_id=session_id
                )
            )

            _display_response(result, stream)

            console.print()

            # Guardar session_id para contexto continuo
            if not session_id and result.get("session_id"):
                session_id = result["session_id"]

        except KeyboardInterrupt:
            console.print("\n[dim]⚠️ Interrumpido por usuario[/dim]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error procesando mensaje: {type(e).__name__}: {e}[/red]")
            console.print("[dim]Tip: Usá /help para ver comandos disponibles[/dim]")
            break

    # Cleanup
    asyncio.run(orchestrator.shutdown())


def _display_response(result: dict, stream: bool):
    """Muestra la respuesta del agente"""
    if result.get("error"):
        console.print(f"[red]❌ Error: {result['error']}[/red]")
        return

    response = result.get("response", result.get("content", str(result)))

    if stream:
        # Streaming token por token (simulado)
        for chunk in _stream_text(response):
            console.print(chunk, end="", highlight=False)
        console.print()
    else:
        # Mostrar respuesta completa con markdown
        console.print(Markdown(response))

    # Mostrar sugerencias si existen
    if result.get("suggestions"):
        console.print("\n[bold]💡 Sugerencias:[/bold]")
        for suggestion in result["suggestions"][:3]:
            console.print(f"  • {suggestion}")


def _show_help():
    """Muestra ayuda de comandos"""
    console.print(Panel(
        "[bold]Comandos disponibles:[/bold]\n\n"
        "[green]/quit[/green], [green]/exit[/green], [green]/q[/green]  - Salir del chat\n"
        "[green]/clear[/green], [green]/cls[/green]              - Limpiar contexto\n"
        "[green]/help[/green], [green]/h[/green]                 - Mostrar esta ayuda\n\n"
        "[dim]Escribí tu mensaje normalmente para conversar con el agente.[/dim]",
        title="📖 Ayuda de Chat",
        style="green"
    ))


def _stream_text(text: str, chunk_size: int = 10):
    """Generador para streaming de texto (simulado)"""
    for i in range(0, len(text), chunk_size):
        yield text[i:i + chunk_size]


if __name__ == '__main__':
    chat_command()