# devmind-core/cli/commands/config.py
"""
Comando de configuración de DevMind Core.

Permite ver y modificar la configuración del agente.
"""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from core.config.manager import ConfigManager

console = Console()


@click.command('config')
@click.option('--show', '-s', is_flag=True, help='Mostrar configuración completa')
@click.option('--set', '-k', 'key_value', nargs=2, help='Establecer valor de configuración')
@click.option('--profile', '-p', type=str, help='Guardar como perfil')
@click.option('--git-name', type=str, help='Configurar nombre de Git')
@click.option('--git-email', type=str, help='Configurar email de Git')
def config_command(show: bool, key_value: tuple, profile: str,git_name: str, git_email: str) -> None:
    """
    ⚙️ Ver y modificar configuración del agente.

    Sin argumentos muestra un resumen. Usa --show para ver todo,
    o --set para modificar valores específicos.
    """
    config_manager = ConfigManager()

    if not config_manager.is_initialized():
        console.print(Panel(
            "❌ Sistema no inicializado.\n\n"
            "Ejecuta: [bold]devmind init[/bold]",
            title="Configuración Requerida",
            style="red"
        ))
        return

    config = config_manager.get_config()

    if git_name or git_email:
        if not config.git_config:
            from core.config.schema import GitConfig
            config.git_config = GitConfig()

        if git_name:
            config.git_config.name = git_name
            console.print(f"✅ Git name: {git_name}")
        if git_email:
            # Validar formato de email
            import re
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', git_email):
                config.git_config.email = git_email
                console.print(f"✅ Git email: {git_email}")
            else:
                console.print("❌ Email inválido")
                return

        config_manager.update_config(git_config=config.git_config)
        console.print("✅ Configuración de Git actualizada")
        return

    # Mostrar configuración completa
    if show:
        import json
        config_dict = config.dict()
        console.print(Panel(
            json.dumps(config_dict, indent=2, default=str),
            title="📋 Configuración Completa",
            style="blue"
        ))
        return

    # Establecer valor
    if key_value:
        key, value = key_value
        if hasattr(config, key):
            try:
                config_manager.update_config(**{key: value})
                console.print(f"✅ {key} actualizado a: {value}")
            except Exception as e:
                console.print(f"❌ Error actualizando {key}: {e}")
        else:
            console.print(f"❌ Clave inválida: {key}")
            console.print("Usa --show para ver claves disponibles")
        return

    # Guardar como perfil
    if profile:
        if config_manager.save_as_profile(profile):
            console.print(f"✅ Configuración guardada como perfil: {profile}")
        else:
            console.print("❌ Error guardando perfil")
        return

    # Mostrar resumen (default)
    _show_config_summary(config)


def _show_config_summary(config) -> None:
    """Muestra resumen de configuración"""
    table = Table(title="⚙️ Configuración Actual")
    table.add_column("Categoría", style="cyan")
    table.add_column("Configuración", style="green")

    table.add_row(
        "Identidad",
        f"{config.agent_name} ({config.personality})"
    )
    table.add_row(
        "Autonomía",
        f"{config.autonomy_mode} (máx {config.max_file_write_without_confirm} archivos)"
    )
    table.add_row(
        "Seguridad",
        f"Sandbox: {'✅' if config.sandbox_enabled else '❌'} | "
        f"Internet: {'✅' if config.allow_internet else '❌'}"
    )
    table.add_row(
        "Agentes",
        f"{'Todos' if config.enable_all_agents else 'Selectivos'} | "
        f"Máx concurrentes: {config.max_concurrent_agents}"
    )
    table.add_row(
        "Aprendizaje",
        f"{'✅' if config.allow_language_learning else '❌'} | "
        f"Modo: {config.learning_mode}"
    )

    console.print(table)
    console.print()
    console.print("💡 Usa [bold]devmind config --show[/bold] para ver todos los detalles")
    console.print("💡 Usa [bold]devmind config --set clave valor[/bold] para modificar")