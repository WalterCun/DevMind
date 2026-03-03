import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys

from core.config.manager import ConfigManager
from core.config.wizard import OnboardingWizard

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def main():
    """🤖 DevMind Core - Tu ingeniero de software autónomo"""
    pass


@main.command()
def init():
    """🧙 Iniciar wizard de configuración"""
    console.print(Panel.fit("🧙‍♂️ Wizard de Configuración Inicial", style="bold blue"))

    config_manager = ConfigManager()
    if config_manager.is_initialized():
        console.print("⚠️  Ya estás inicializado. Usa 'devmind reset' para reiniciar.")
        return

    wizard = OnboardingWizard()
    wizard.run()


@main.command()
@click.argument('message', required=False)
@click.option('--project', '-p', help='ID del proyecto')
@click.option('--mode', '-m', type=click.Choice(['chat', 'plan', 'code', 'fix']), default='chat')
def chat(message, project, mode):
    """💬 Iniciar sesión de chat"""
    config_manager = ConfigManager()
    if not config_manager.is_initialized():
        console.print("❌ Debes inicializar primero. Usa: devmind init")
        return

    console.print(Panel.fit(f"💬 Modo: {mode.upper()}", style="bold green"))

    # Implementar loop de chat interactivo
    from cli.commands.chat import ChatSession
    session = ChatSession(project_id=project, mode=mode)
    session.run(message)


@main.command()
@click.option('--project', '-p', required=True)
def status(project):
    """📊 Ver estado del proyecto"""
    from core.memory.relational_store import RelationalMemory

    memory = RelationalMemory()
    status = memory.get_project_status(project)

    if not status:
        console.print("❌ Proyecto no encontrado")
        return

    # Mostrar tabla de estado
    table = Table(title=f"Estado: {status['project']['name']}")
    table.add_column("Métrica", style="cyan")
    table.add_column("Valor", style="green")

    table.add_row("Estado", status['project']['status'])
    table.add_row("Viabilidad", f"{status['project']['viability_score'] or 'N/A'}")
    table.add_row("Fases", f"{len(status['phases'])}")
    table.add_row("Tareas Totales", str(status['tasks']['total']))
    table.add_row("Tareas Completadas", str(status['tasks']['done']))
    table.add_row("Bugs Abiertos", str(status['bugs']['open']))

    console.print(table)


@main.command()
def agents():
    """🤖 Ver estado de agentes"""
    from core.agents.registry import AgentRegistry

    registry = AgentRegistry()
    summary = registry.get_status_summary()

    table = Table(title=f"Agentes Activos: {summary['total']}")
    table.add_column("Nombre", style="cyan")
    table.add_column("Rol", style="magenta")
    table.add_column("Nivel", style="yellow")
    table.add_column("Estado", style="green")
    table.add_column("Tareas", style="blue")

    for agent in summary['agents']:
        table.add_row(
            agent['name'],
            agent['role'],
            str(agent['level']),
            agent['status'],
            f"{agent['tasks_completed']}/{agent['tasks_failed']}"
        )

    console.print(table)


@main.command()
def reset():
    """🔄 Resetear configuración"""
    if click.confirm('¿Estás seguro? Se perderá toda la configuración.'):
        config_manager = ConfigManager()
        config_manager.reset_config()
        console.print("✅ Configuración reseteada. Usa 'devmind init' para reiniciar.")


if __name__ == '__main__':
    main()