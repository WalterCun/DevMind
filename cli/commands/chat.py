# devmind-core/cli/commands/chat.py
"""
Comando chat para DevMind Core.
Proporciona interfaz interactiva de conversación con el agente.
"""

import asyncio

import click
from rich.console import Console
from rich.json import JSON
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
@click.option('--json', '-j', 'output_json', is_flag=True, help='✅ Mostrar respuesta en JSON (default: texto natural)')
@click.argument('initial_message', nargs=1, required=False)
def chat_command(project_id: str, clear: bool, stream: bool, output_json: bool, initial_message: str):
    """💬 Conversación interactiva con el agente

    Ejemplos:
      devmind chat                          # Modo interactivo
      devmind chat "Hola"                   # Mensaje inicial
      devmind chat -p myproject "Planificar API"
      devmind chat --json "Mostrar config"
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

        # Mostrar banner (solo en modo interactivo o sin mensaje inicial)
    if not initial_message:
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
                session_id=session_id,
                output_json=output_json
            )
        )

        _display_response(result, stream, output_json)

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

            # Toggle JSON mode con comando
            if user_input.lower() == '/json':
                output_json = not output_json
                console.print(
                    f"[dim]📋 Modo JSON: {'[green]Activado[/green]' if output_json else '[yellow]Desactivado[/yellow]'}[/dim]")
                continue

            # Procesar mensaje
            console.print()
            console.print("[bold blue]Jarvis[/bold blue] está pensando...")

            result = asyncio.run(
                orchestrator.process_message(
                    message=user_input,
                    session_id=session_id,
                    output_json=output_json  # ✅ Pasar flag JSON
                )
            )

            _display_response(result, stream, output_json)

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


def _display_response(result: dict, stream: bool, output_json: bool):
    """Muestra la respuesta del agente con formato adecuado"""

    if result.get("error"):
        console.print(f"[red]❌ Error: {result['error']}[/red]")
        return

    # ✅ Si se solicitó JSON, mostrar raw JSON
    if output_json:
        console.print(JSON.from_data(result, indent=2))
        return

    # ✅ Formato natural por defecto
    response = result.get("response") or result.get("content", "")

    # Si response es un string que parece JSON, intentar parsear y formatear
    if isinstance(response, str) and response.strip().startswith("{"):
        try:
            import json
            parsed = json.loads(response)

            # ✅ Extraer contenido legible del JSON
            if isinstance(parsed, dict):
                # Buscar campos comunes de contenido
                content_fields = ['content', 'response', 'answer', 'output_text', 'message']
                for field in content_fields:
                    if field in parsed:
                        response = parsed[field]
                        break
                else:
                    # Si no hay campo obvio, formatear como texto estructurado
                    response = _format_structured_data(parsed)
            else:
                response = str(parsed)

        except (json.JSONDecodeError, Exception):
            pass  # Mantener response original si falla el parseo

    # Mostrar respuesta formateada
    if stream:
        for chunk in _stream_text(response):
            console.print(chunk, end="", highlight=False)
        console.print()
    else:
        # ✅ Usar Markdown para mejor formato
        console.print(Markdown(response))

    # Mostrar sugerencias si existen (solo en modo natural)
    if result.get("suggestions"):
        console.print("\n[bold]💡 Sugerencias:[/bold]")
        for suggestion in result["suggestions"][:3]:
            console.print(f"  • {suggestion}")


def _format_structured_data(data: dict, indent: int = 0) -> str:
    """Convierte datos estructurados a texto legible"""
    lines = []
    prefix = "  " * indent

    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{prefix}[bold]{key}:[/bold]")
            lines.append(_format_structured_data(value, indent + 1))
        elif isinstance(value, list):
            lines.append(f"{prefix}[bold]{key}:[/bold]")
            for item in value:
                if isinstance(item, dict):
                    lines.append(f"{prefix}  • {_format_structured_data(item, 0)}")
                else:
                    lines.append(f"{prefix}  • {item}")
        else:
            lines.append(f"{prefix}[bold]{key}:[/bold] {value}")

    return "\n".join(lines)


def _show_help():
    """Muestra ayuda de comandos"""
    console.print(Panel(
        "[bold]Comandos disponibles:[/bold]\n\n"
        "[green]/quit[/green], [green]/exit[/green], [green]/q[/green]  - Salir del chat\n"
        "[green]/clear[/green], [green]/cls[/green]              - Limpiar contexto\n"
        "[green]/json[/green]                         - Toggle modo JSON\n"
        "[green]/help[/green], [green]/h[/green]                 - Mostrar esta ayuda\n\n"
        "[dim]Opciones de línea de comandos:[/dim]\n"
        "[dim]  --json, -j    Mostrar respuesta en formato JSON[/dim]\n"
        "[dim]  --project, -p ID del proyecto[/dim]\n"
        "[dim]  --stream, -s  Streaming token por token[/dim]\n\n"
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