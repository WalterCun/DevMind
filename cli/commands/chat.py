# cli/commands/chat.py
"""
Comando chat para DevMind Core.
Proporciona interfaz interactiva de conversación con el agente.
"""

import asyncio
import os
import sys
from pathlib import Path

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt

from cli.context import ContextManager
from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator

console = Console()


@click.command('chat')
@click.option('--project', '-p', 'project_path', type=click.Path(), default=".", help='Directorio del proyecto')
@click.option('--clear', '-c', is_flag=True, help='Limpiar contexto e iniciar nuevo')
@click.option('--stream', '-s', is_flag=True, help='Streaming de respuesta token por token')
@click.option('--json', '-j', 'output_json', is_flag=True, help='Mostrar respuesta en JSON (default: texto natural)')
@click.argument('initial_message', nargs=1, required=False)
def chat_command(project_path: str, clear: bool, stream: bool, output_json: bool, initial_message: str):
    """💬 Conversación interactiva con el agente

    Ejemplos:
      devmind chat                          # Modo interactivo
      devmind chat "Hola"                   # Mensaje inicial
      devmind chat -p myproject "Planificar API"
      devmind chat --json "Mostrar config"
    """

    # 1. Configuración del Contexto del Proyecto
    target_path = Path(project_path)

    # Crear directorio si no existe
    if not target_path.exists():
        console.print(f"[yellow]Directorio no encontrado. Creando: {target_path.resolve()}[/yellow]")
        try:
            target_path.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            console.print(f"[red]❌ Error creando directorio: {e}[/red]")
            return

    abs_project_path = str(target_path.resolve())
    os.environ["PROJECT_ROOT"] = abs_project_path

    # 2. Cargar Configuración
    config_manager = ConfigManager()
    if not config_manager.is_initialized():
        console.print(Panel(
            "[yellow]⚠️ Configuración no inicializada[/yellow]\n"
            "Ejecutá [bold]devmind init[/bold] primero",
            style="yellow"
        ))
        return

    config = config_manager.get_config()

    console.print(Panel.fit(
        f"[bold]💬 Modo:[/bold] CHAT\n"
        f"[bold]🤖 Agente:[/bold] {config.agent_name}\n"
        f"[bold]⚡ Autonomía:[/bold] {config.autonomy_mode.value}\n"
        f"[bold green]📂 Proyecto:[/bold green] {abs_project_path}",
        title="DevMind Chat",
        style="cyan"
    ))
    console.print()

    # 3. Inicializar Orquestador
    orchestrator = DevMindOrchestrator(
        project_id=target_path.name,  # Usar nombre de carpeta como ID
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando el orchestrator[/red]")
        return

    # 4. Manejar limpieza de contexto
    context_manager = ContextManager()
    if clear:
        context_manager.clear()
        console.print("[dim]🧹 Contexto limpiado.[/dim] \n")

    session_id = None

    # 5. Procesar mensaje inicial si existe
    if initial_message:
        console.print(f"[bold green]Tú[/bold green]: {initial_message}")
        console.print()

        with console.status("[bold blue]Jarvis está pensando y actuando...[/bold blue]", spinner="dots"):
            result = asyncio.run(
                orchestrator.execute_autonomous_task(
                    task=initial_message,
                    session_id=session_id
                )
            )

        _display_response(result, output_json)
        session_id = result.get("session_id")
        console.print()

    # 6. Bucle Principal Interactivo
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

            if user_input.lower() in ['/clear', '/cls']:
                console.print("[dim]🧹 Contexto limpiado[/dim]")
                session_id = None
                continue

            # Toggle JSON mode con comando
            if user_input.lower() == '/json':
                output_json = not output_json
                console.print(
                    f"[dim]📋 Modo JSON: {'[green]Activado[/green]' if output_json else '[yellow]Desactivado[/yellow]'}[/dim]")
                continue

            # Procesar mensaje con el orquestador autónomo
            console.print()

            with console.status("[bold blue]Jarvis está pensando y actuando...[/bold blue]", spinner="dots"):
                try:
                    result = asyncio.run(
                        orchestrator.execute_autonomous_task(
                            task=user_input,
                            session_id=session_id
                        )
                    )
                except KeyboardInterrupt:
                    # Manejar Ctrl+C durante la ejecución
                    console.print("\n[yellow]⚠️ Ejecución interrumpida por el usuario[/yellow]")
                    continue
                except Exception as e:
                    console.print(f"\n[red]❌ Error crítico en ejecución: {str(e)}[/red]")
                    logger.error(f"Error en execute_autonomous_task: {e}", exc_info=True)
                    continue

            # Mostrar respuesta
            _display_response(result, output_json)
            console.print()

            # Guardar session_id para contexto continuo
            if not session_id and result.get("session_id"):
                session_id = result["session_id"]

        except KeyboardInterrupt:
            console.print("\n[dim]👋 Saliendo... (Presiona Ctrl+C de nuevo para forzar salida)[/dim]")
            break
        except Exception as e:
            console.print(f"[red]❌ Error inesperado: {str(e)}[/red]")
            logger.error(f"Error en loop principal de chat: {e}", exc_info=True)
            break

    # Cleanup
    try:
        asyncio.run(orchestrator.shutdown())
    except:
        pass


def _display_response(result: dict, output_json: bool = False) -> None:
    """Muestra la respuesta del agente con formato adecuado"""

    if result.get("error"):
        console.print(f"[red]❌ Error: {result['error']}[/red]")
        return

    # Si se solicitó JSON, mostrar raw JSON
    if output_json:
        from rich.json import JSON
        import json
        console.print(JSON.from_data(result, indent=2))
        return

    # Formato natural por defecto
    response = result.get("response") or result.get("content", "")

    # Si response es un string que parece JSON, intentar parsear y formatear
    if isinstance(response, str) and response.strip().startswith("{"):
        try:
            import json
            parsed = json.loads(response)

            # Extraer contenido legible del JSON
            if isinstance(parsed, dict):
                content_fields = ['content', 'response', 'answer', 'output_text', 'message']
                for field in content_fields:
                    if field in parsed:
                        response = parsed[field]
                        break
                else:
                    # Si no hay campo obvio, usar el JSON formateado
                    response = f"```json\n{json.dumps(parsed, indent=2)}\n```"
        except (json.JSONDecodeError, Exception):
            pass  # Mantener response original si falla el parseo

    # Mostrar respuesta formateada como Markdown
    console.print("[bold blue]Jarvis[/bold blue]:")
    console.print(Markdown(response))

    # Mostrar información de iteraciones si fue tarea autónoma
    if result.get("iterations", 0) > 1:
        console.print(f"\n[dim]ℹ️ Tarea completada en {result['iterations']} pasos autónomos.[/dim]")

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


if __name__ == '__main__':
    chat_command()