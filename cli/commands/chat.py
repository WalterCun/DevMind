# devmind-core/cli/commands/chat.py
"""
Comando de chat integrado con el orchestrator.

Permite conversación interactiva con el agente DevMind,
con contexto persistente y streaming de respuestas.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.prompt import Prompt

from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator
from cli.context import ContextManager, SessionContext
from cli.streaming import stream_agent_response, StreamingResponse

console = Console()


@click.command('chat')
@click.argument('message', required=False)
@click.option('--project', '-p', 'project_id', help='ID del proyecto')
@click.option('--mode', '-m', type=click.Choice(['chat', 'plan', 'code', 'fix']), default='chat')
@click.option('--session', '-s', 'session_id', help='ID de sesión para continuar')
@click.option('--no-stream', is_flag=True, help='Desactivar streaming, mostrar respuesta completa')
def chat_command(
        message: str,
        project_id: str,
        mode: str,
        session_id: str,
        no_stream: bool
) -> None:
    """
    💬 Iniciar sesión de chat con el agente DevMind.

    Puedes enviar un mensaje inicial como argumento o entrar en modo interactivo.

    Ejemplos:

        devmind chat
        devmind chat "Quiero crear una API para hoteles"
        devmind chat --project my-hotel-api --mode code
        devmind chat --session abc123  # Continuar sesión anterior
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

    # Mostrar header
    _show_chat_header(config, mode, project_id)

    # Inicializar contexto de sesión
    context_manager = ContextManager()

    if session_id:
        session = context_manager.load_session(session_id)
        if session:
            console.print(f"[dim]📌 Sesión cargada: {session_id}[/dim]")
        else:
            console.print(f"[yellow]⚠️  Sesión no encontrada, creando nueva[/yellow]")
            session = context_manager.create_session(project_id=project_id, mode=mode)
    else:
        session = context_manager.get_or_create_session(project_id=project_id, mode=mode)

    # Inicializar orchestrator
    orchestrator = DevMindOrchestrator(
        project_id=session.project_id,
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando el orchestrator[/red]")
        return

    # Si hay mensaje inicial, procesarlo
    if message:
        console.print(f"[bold blue]Tú:[/bold blue] {message}")
        asyncio.run(
            _process_message(orchestrator, context_manager, message, session.session_id, no_stream, config.agent_name)
        )
        return

    # Modo interactivo
    console.print(
        "\n[dim]Escribe tus mensajes. Usa [/dim][bold]/help[/bold][dim] para comandos, [/dim][bold]/quit[/bold][dim] para salir.\n[/dim]")

    while True:
        try:
            user_input = Prompt.ask(
                "[bold blue]Tú[/bold blue]",
                default=""
            ).strip()

            if not user_input:
                continue

            if user_input.lower() in ['/quit', '/exit', '/q']:
                _show_goodbye(config.agent_name)
                break

            if user_input.lower() == '/help':
                _show_help()
                continue

            if user_input.startswith('/mode '):
                new_mode = user_input.split(' ', 1)[1].strip()
                try:
                    session.set_mode(new_mode)
                    session.save()
                    console.print(f"[green]✅ Modo cambiado a: {new_mode}[/green]")
                except ValueError as e:
                    console.print(f"[red]❌ {e}[/red]")
                continue

            if user_input.startswith('/project '):
                new_project = user_input.split(' ', 1)[1].strip()
                session.set_project(new_project)
                session.save()
                console.print(f"[green]✅ Proyecto cambiado a: {new_project}[/green]")
                continue

            if user_input == '/clear':
                session.clear_history()
                session.save()
                console.print("[green]✅ Historial limpiado[/green]")
                continue

            if user_input == '/context':
                _show_context(session)
                continue

            # Procesar mensaje
            asyncio.run(
                _process_message(orchestrator, context_manager, user_input, session.session_id, no_stream,
                                 config.agent_name)
            )

        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Interrumpido por el usuario[/yellow]")
            continue
        except EOFError:
            _show_goodbye(config.agent_name)
            break
        except Exception as e:
            console.print(f"[red]❌ Error: {str(e)}[/red]")
            console.print_exception(show_locals=False)


async def _process_message(
        orchestrator: DevMindOrchestrator,
        context_manager: ContextManager,
        message: str,
        session_id: str,
        no_stream: bool,
        agent_name: str
) -> None:
    """Procesa un mensaje y muestra la respuesta"""
    # Guardar mensaje del usuario
    context_manager.add_message("user", message)

    try:
        if no_stream:
            # Modo sin streaming
            result = await orchestrator.process_message(
                message=message,
                session_id=session_id
            )
            console.print(f"\n[bold green]{agent_name}:[/bold green]")
            console.print(Markdown(result.get("response", "Sin respuesta")))
        else:
            # Modo con streaming
            from cli.streaming import stream_agent_response
            result = await stream_agent_response(
                orchestrator=orchestrator,
                message=message,
                session_id=session_id,
                agent_name=agent_name
            )

        # Guardar respuesta del agente
        if result:
            context_manager.add_message(
                "agent",
                result.get("response", ""),
                intent=result.get("intent"),
                metadata={
                    "files_modified": result.get("files_modified", []),
                    "suggestions": result.get("suggestions", [])
                }
            )

            # Mostrar archivos modificados si los hay
            if result.get("files_modified"):
                console.print("\n[bold blue]📁 Archivos modificados:[/bold blue]")
                for file in result["files_modified"]:
                    console.print(f"  • {file.get('path', 'unknown')}")

            # Mostrar sugerencias si las hay
            if result.get("suggestions"):
                console.print("\n[bold yellow]💡 Sugerencias:[/bold yellow]")
                for suggestion in result["suggestions"]:
                    console.print(f"  • {suggestion}")

    except Exception as e:
        console.print(f"\n[red]❌ Error procesando mensaje: {str(e)}[/red]")
        context_manager.add_message(
            "system",
            f"Error: {str(e)}",
            metadata={"error": True}
        )


def _show_chat_header(config, mode: str, project_id: str) -> None:
    """Muestra header del chat"""
    header_lines = [
        f"[bold green]💬 Modo:[/bold green] {mode.upper()}",
        f"[bold green]🤖 Agente:[/bold green] {config.agent_name}",
        f"[bold green]⚡ Autonomía:[/bold green] {config.autonomy_mode}",
    ]

    if project_id:
        header_lines.append(f"[bold green]📁 Proyecto:[/bold green] {project_id}")

    console.print(Panel(
        "\n".join(header_lines),
        title="DevMind Chat",
        style="green",
        border_style="bright_green"
    ))


def _show_help() -> None:
    """Muestra ayuda de comandos"""
    help_text = """
## Comandos Disponibles

| Comando | Descripción |
|---------|-------------|
| `/help` | Mostrar esta ayuda |
| `/quit` | Salir del chat |
| `/clear` | Limpiar historial de conversación |
| `/context` | Mostrar contexto actual de la sesión |
| `/mode <modo>` | Cambiar modo (chat, plan, code, fix) |
| `/project <id>` | Cambiar proyecto activo |

## Consejos

- Sé específico en tus solicitudes
- Proporciona contexto cuando sea relevante
- Usa `/mode code` para generación de código
- Usa `/mode fix` para reportar bugs
- Usa `/clear` para empezar de cero sin salir
"""
    console.print(Markdown(help_text))


def _show_context(session: SessionContext) -> None:
    """Muestra contexto actual de la sesión"""
    console.print(Panel(
        f"[bold]Sesión:[/bold] {session.session_id}\n"
        f"[bold]Proyecto:[/bold] {session.project_id or 'No asignado'}\n"
        f"[bold]Modo:[/bold] {session.mode}\n"
        f"[bold]Mensajes:[/bold] {len(session.message_history)}\n"
        f"[bold]Creada:[/bold] {session.created_at.strftime('%Y-%m-%d %H:%M')}",
        title="📋 Contexto de Sesión",
        style="blue"
    ))


def _show_goodbye(agent_name: str) -> None:
    """Muestra mensaje de despedida"""
    console.print(Panel(
        f"\n[bold]👋 ¡Hasta luego![/bold]\n\n"
        f"Fui [bold]{agent_name}[/bold], tu agente de desarrollo.\n"
        f"Tu sesión está guardada. Usa [bold]devmind chat --session <id>[/bold] para continuar.\n",
        style="green"
    ))