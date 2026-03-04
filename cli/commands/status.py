# devmind-core/cli/commands/status.py
"""
Comando de estado de DevMind Core.

Muestra el estado actual del sistema, configuración completa y métricas.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from core.config.manager import ConfigManager

console = Console()


@click.command('status')
@click.option('--full', '-f', is_flag=True, help='Mostrar configuración completa en formato JSON')
@click.option('--section', '-s', type=click.Choice(['identity', 'capabilities', 'tools', 'system', 'all']),
              default='all', help='Mostrar solo una sección específica')
def status_command(full: bool, section: str) -> None:
    """
    📊 Ver estado del sistema y configuración.

    Muestra información sobre la configuración actual,
    agentes disponibles, herramientas y estado del sistema.
    """
    config_manager = ConfigManager()

    if not config_manager.is_initialized():
        console.print(Panel(
            "❌ Sistema no inicializado.\n\n"
            "Ejecuta: [bold]devmind init[/bold]",
            title="Estado del Sistema",
            style="red"
        ))
        return

    config = config_manager.get_config()

    # Modo completo: mostrar JSON raw
    if full:
        import json
        config_dict = config.model_dump(mode='json')
        console.print(Panel(
            json.dumps(config_dict, indent=2, ensure_ascii=False),
            title="📋 Configuración Completa (JSON)",
            style="blue",
            width=120
        ))
        return

    # Mostrar secciones según filtro
    if section in ['all', 'identity']:
        _show_identity_section(config)
    if section in ['all', 'capabilities']:
        _show_capabilities_section(config)
    if section in ['all', 'tools']:
        _show_tools_section(config)  # ✅ NUEVO: Incluye Git
    if section in ['all', 'system']:
        _show_system_section(config)

    # Panel de rutas y sistema
    _show_system_paths()

    # ✅ NUEVO: Estado de Ollama y servicios
    _show_services_status()


def _show_identity_section(config) -> None:
    """Muestra sección de identidad del agente"""
    table = Table(title="🤖 Identidad del Agente")
    table.add_column("Propiedad", style="cyan", width=25)
    table.add_column("Valor", style="green")

    table.add_row("Nombre", config.agent_name)
    table.add_row("Personalidad", config.personality)
    table.add_row("Estilo de Comunicación", config.communication_style)
    table.add_row("Modo de Autonomía", config.autonomy_mode)

    # ✅ Mostrar firma Git si está configurada
    git_sig = config.get_git_signature()
    if git_sig:
        table.add_row("Firma Git", git_sig)
    else:
        table.add_row("Firma Git", "[yellow]No configurada[/yellow] (usa: devmind config --git-name/email)")

    console.print(table)
    console.print()


def _show_capabilities_section(config) -> None:
    """Muestra sección de capacidades"""
    table = Table(title="⚡ Capacidades")
    table.add_column("Capacidad", style="cyan", width=25)
    table.add_column("Estado", style="green", width=10)
    table.add_column("Detalle", style="dim")

    table.add_row(
        "Sandbox Docker",
        "✅" if config.sandbox_enabled else "❌",
        "Ejecución aislada de código" if config.sandbox_enabled else "Código se ejecuta localmente"
    )
    table.add_row(
        "Acceso a Internet",
        "✅" if config.allow_internet else "❌",
        "Descarga de docs/paquetes" if config.allow_internet else "Solo recursos locales"
    )
    table.add_row(
        "Email",
        "✅" if config.allow_email else "❌",
        f"SMTP: {config.email_config.smtp_server[:20]}..." if config.email_config else "No configurado"
    )
    table.add_row(
        "Auto-Mejora",
        "✅" if config.allow_self_improvement else "❌",
        "Creación automática de herramientas" if config.allow_self_improvement else "Herramientas manuales"
    )
    table.add_row(
        "Aprendizaje de Lenguajes",
        "✅" if config.allow_language_learning else "❌",
        f"Modo: {config.learning_mode}" if config.allow_language_learning else "Solo lenguajes conocidos"
    )

    console.print(table)
    console.print()


def _show_tools_section(config) -> None:
    """✅ NUEVO: Muestra sección de herramientas externas"""
    table = Table(title="🛠️ Herramientas y Integraciones")
    table.add_column("Herramienta", style="cyan", width=20)
    table.add_column("Estado", style="green", width=10)
    table.add_column("Configuración", style="dim")

    # Git Configuration
    if config.git_config and config.git_config.is_configured:
        table.add_row(
            "Git",
            "✅",
            f"{config.git_config.name} <{config.git_config.email}>"
        )
    else:
        table.add_row(
            "Git",
            "[yellow]Pendiente[/yellow]",
            "Usa: devmind config --git-name/email"
        )

    # Browser/Navegación
    browser_status = {
        'headless': '🔒 Headless (sin UI)',
        'persistent': '💾 Persistente (con sesión)',
        'disabled': '🚫 Deshabilitado'
    }
    table.add_row(
        "Navegador",
        "✅" if config.browser_profile != 'disabled' else "❌",
        browser_status.get(config.browser_profile, config.browser_profile)
    )

    # IDE Integration
    table.add_row(
        "IDE Integration",
        "✅" if config.ide_integration else "❌",
        "VS Code / JetBrains" if config.ide_integration else "Sin integración"
    )

    # Email (detalles)
    if config.allow_email and config.email_config:
        table.add_row(
            "SMTP Server",
            "✅",
            f"{config.email_config.smtp_server}:{config.email_config.smtp_port}"
        )

    # Documentation Sources
    sources = config.documentation_sources
    if sources:
        table.add_row(
            "Fuentes de Docs",
            f"[green]{len(sources)}[/green]",
            ", ".join(sources[:3]) + ("..." if len(sources) > 3 else "")
        )

    console.print(table)
    console.print()


def _show_system_section(config) -> None:
    """Muestra sección de configuración del sistema"""
    table = Table(title="⚙️ Configuración del Sistema")
    table.add_column("Parámetro", style="cyan", width=30)
    table.add_column("Valor", style="green")

    table.add_row("Máximo Agentes Concurrentes", str(config.max_concurrent_agents))
    table.add_row("Máximo Archivos sin Confirmar", str(config.max_file_write_without_confirm))
    table.add_row("Nivel de Logging", config.log_level)
    table.add_row("Frecuencia de Auditoría", config.audit_frequency)

    # Lenguajes con emojis
    lang_emojis = {
        'python': '🐍', 'javascript': '📜', 'typescript': '📘',
        'rust': '🦀', 'java': '☕', 'php': '🐘', 'go': '🔹',
        'csharp': '🔷', 'cpp': '🐛', 'ruby': '🦎'
    }
    langs_display = [
        f"{lang_emojis.get(lang, '•')} {lang}"
        for lang in config.preferred_languages
    ]
    table.add_row("Lenguajes Conocidos", ", ".join(langs_display))

    # Agentes prioritarios
    if config.priority_agents:
        table.add_row("Agentes Prioritarios", ", ".join(config.priority_agents))
    elif config.enable_all_agents:
        table.add_row("Agentes Activos", "[green]Todos[/green] (12 agentes)")
    else:
        table.add_row("Agentes Activos", "[yellow]Selectivos[/yellow]")

    console.print(table)
    console.print()


def _show_system_paths() -> None:
    """Muestra panel de rutas del sistema"""
    from core.config.manager import ConfigManager as CM

    panel = Panel(
        Text.assemble(
            ("📁 Configuración: ", "bold"),
            (str(CM.CONFIG_FILE), "green"),
            "\n",
            ("📁 Proyectos: ", "bold"),
            (str(CM.CONFIG_DIR / "projects"), "green"),
            "\n",
            ("📁 Perfiles: ", "bold"),
            (str(CM.PROFILES_DIR), "green"),
            "\n",
            ("📁 Memoria: ", "bold"),
            (str(CM.CONFIG_DIR / ".memory"), "green"),
        ),
        title="📂 Rutas del Sistema",
        style="blue",
        expand=False
    )
    console.print(panel)
    console.print()


def _show_services_status() -> None:
    """✅ NUEVO: Verifica estado de servicios externos (Ollama, Docker, etc.)"""
    import subprocess
    import shutil

    table = Table(title="🔌 Estado de Servicios")
    table.add_column("Servicio", style="cyan", width=20)
    table.add_column("Estado", style="green", width=15)
    table.add_column("Detalle", style="dim")

    # Verificar Ollama
    try:
        result = subprocess.run(
            ["curl", "-s", "http://localhost:11434/api/tags"],
            capture_output=True,
            text=True,
            timeout=3
        )
        if result.returncode == 0 and "models" in result.stdout:
            table.add_row("Ollama", "✅ Online", "LLM local disponible")
        else:
            table.add_row("Ollama", "⚠️ Sin respuesta", "Ejecuta: ollama serve")
    except FileNotFoundError:
        table.add_row("Ollama", "❌ curl no encontrado", "Instala curl para verificación")
    except Exception as e:
        table.add_row("Ollama", f"❌ Error", str(e)[:30])

    # Verificar Docker
    if shutil.which("docker"):
        try:
            result = subprocess.run(
                ["docker", "ps", "--format", "{{.Names}}"],
                capture_output=True,
                text=True,
                timeout=3
            )
            if result.returncode == 0:
                containers = [c for c in result.stdout.split('\n') if 'devmind' in c.lower()]
                if containers:
                    table.add_row("Docker", "✅ Running", f"Contenedores: {', '.join(containers)}")
                else:
                    table.add_row("Docker", "✅ Installed", "Sin contenedores DevMind activos")
            else:
                table.add_row("Docker", "⚠️ Sin permisos", "Verifica acceso a Docker")
        except Exception as e:
            table.add_row("Docker", "❌ Error", str(e)[:30])
    else:
        table.add_row("Docker", "❌ No instalado", "Requerido para sandbox")

    # Verificar ChromaDB (puerto)
    import socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    chroma_status = sock.connect_ex(('localhost', 8000)) == 0
    sock.close()
    table.add_row(
        "ChromaDB",
        "✅ Online" if chroma_status else "⚠️ Puerto 8000",
        "Memoria vectorial"
    )

    # Verificar PostgreSQL (puerto)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    pg_status = sock.connect_ex(('localhost', 5432)) == 0
    sock.close()
    table.add_row(
        "PostgreSQL",
        "✅ Online" if pg_status else "⚠️ Puerto 5432",
        "Memoria relacional"
    )

    console.print(table)
    console.print()

    # 💡 Tips si hay servicios caídos
    warnings = []
    if not chroma_status:
        warnings.append("• ChromaDB: docker-compose up -d chromadb")
    if not pg_status:
        warnings.append("• PostgreSQL: docker-compose up -d postgres")

    if warnings:
        console.print(Panel(
            "\n".join(warnings),
            title="💡 Tips para iniciar servicios",
            style="yellow",
            expand=False
        ))
        console.print()