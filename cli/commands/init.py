# devmind-core/cli/commands/init.py
"""
Comando de inicialización de DevMind Core.

Ejecuta el wizard de configuración inicial para nuevos usuarios.
"""

import click
from rich.console import Console
from rich.panel import Panel

from core.config.manager import ConfigManager
from core.config.wizard import OnboardingWizard

console = Console()


@click.command('init')
@click.option('--reset', '-r', is_flag=True, help='Resetear configuración existente')
@click.option('--profile', '-p', type=str, help='Cargar perfil predefinido')
@click.option('--resume', '-c', is_flag=True, help='Continuar wizard interrumpido')
def init_command(reset: bool, profile: str, resume: bool) -> None:
    """
    🧙 Iniciar wizard de configuración inicial.

    Este comando guía al usuario a través de la configuración de identidad,
    capacidades y preferencias del agente DevMind.
    """
    config_manager = ConfigManager()

    # Verificar si ya está inicializado
    if config_manager.is_initialized() and not reset:
        console.print(Panel(
            "⚠️  Ya estás inicializado.\n\n"
            "Usa [bold]devmind init --reset[/bold] para reiniciar la configuración.\n"
            "Usa [bold]devmind config[/bold] para modificar la configuración actual.",
            title="Configuración Existente",
            style="yellow"
        ))
        return

    # Resetear si se solicita
    if reset:
        if click.confirm('¿Estás seguro? Se perderá toda la configuración actual.'):
            config_manager.reset_config()
            console.print("✅ Configuración reseteada.\n")
        else:
            console.print("❌ Operación cancelada.")
            return

    # Cargar perfil si se especifica
    if profile:
        console.print(f"📦 Cargando perfil: {profile}")
        profile_config = config_manager.load_profile(profile)
        if profile_config:
            config_manager._config = profile_config
            config_manager._save_config()
            console.print(f"✅ Perfil '{profile}' cargado exitosamente.")
            console.print("💡 Usa 'devmind config' para ajustar detalles.")
            return
        else:
            console.print(f"❌ Perfil '{profile}' no encontrado.")
            return

    # Ejecutar wizard
    console.print(Panel.fit(
        "🧙‍♂️ Wizard de Configuración Inicial",
        style="bold blue"
    ))
    console.print()

    wizard = OnboardingWizard(resume=resume)  # ✅ Pasar flag de resume
    wizard.run(resume=resume)  # ✅ Pasar flag de resume