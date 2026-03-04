# devmind-core/cli/commands/addons.py
"""
Comandos CLI para gestión de addons.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from core.addons.loader import AddonLoader
from core.addons.registry import AddonRegistry

console = Console()


@click.group('addons')
def addons_group():
    """🔌 Gestión de addons y extensiones"""
    pass


@addons_group.command('list')
@click.option('--active', '-a', is_flag=True, help='Solo addons activos')
@click.option('--inactive', '-i', is_flag=True, help='Solo addons inactivos')
def addons_list(active: bool, inactive: bool):
    """📋 Listar addons instalados"""

    registry = AddonRegistry()
    addons = registry.list_addons(
        active_only=active,
        inactive_only=inactive
    )

    if not addons:
        filter_msg = ""
        if active:
            filter_msg = " activos"
        elif inactive:
            filter_msg = " inactivos"

        console.print(Panel(
            f"[yellow]No se encontraron addons{filter_msg}[/yellow]",
            style="yellow"
        ))
        return

    table = Table(title=f"🔌 Addons ({len(addons)})")
    table.add_column("Nombre", style="cyan", width=25)
    table.add_column("Versión", width=10)
    table.add_column("Estado", width=12)
    table.add_column("Autor", width=15)
    table.add_column("Descripción", style="dim")

    for addon in addons:
        status = "[green]✅ Activo[/green]" if addon.get("active") else "[dim]⏸️ Inactivo[/dim]"

        table.add_row(
            addon.get("name", "Unknown"),
            addon.get("version", "1.0.0"),
            status,
            addon.get("author", "unknown"),
            addon.get("description", "")[:40] + "..."
        )

    console.print(table)


@addons_group.command('activate')
@click.argument('name')
def addons_activate(name: str):
    """✅ Activar un addon"""

    registry = AddonRegistry()

    if not registry.get(name):
        console.print(Panel(
            f"[red]Addon '{name}' no encontrado[/red]",
            style="red"
        ))
        return

    console.print(f"[dim]Activando {name}...[/dim]")

    success = registry.activate(name)

    if success:
        console.print(f"[green]✅ Addon '{name}' activado[/green]")
    else:
        console.print(f"[red]❌ Error activando '{name}'[/red]")


@addons_group.command('deactivate')
@click.argument('name')
def addons_deactivate(name: str):
    """⏸️ Desactivar un addon"""

    registry = AddonRegistry()

    if not registry.get(name):
        console.print(Panel(
            f"[red]Addon '{name}' no encontrado[/red]",
            style="red"
        ))
        return

    console.print(f"[dim]Desactivando {name}...[/dim]")

    success = registry.deactivate(name)

    if success:
        console.print(f"[green]✅ Addon '{name}' desactivado[/green]")
    else:
        console.print(f"[red]❌ Error desactivando '{name}'[/red]")


@addons_group.command('install')
@click.argument('path')
def addons_install(path: str):
    """📦 Instalar addon desde ruta"""

    from pathlib import Path
    registry = AddonRegistry()

    addon_path = Path(path)

    if not addon_path.exists():
        console.print(Panel(
            f"[red]Ruta '{path}' no existe[/red]",
            style="red"
        ))
        return

    console.print(f"[dim]Instalando addon desde {path}...[/dim]")

    loaded = registry.load_from_directory(addon_path.parent)

    if loaded > 0:
        console.print(f"[green]✅ {loaded} addon(s) instalado(s)[/green]")
    else:
        console.print("[yellow]⚠️ No se pudieron cargar addons[/yellow]")


@addons_group.command('uninstall')
@click.argument('name')
@click.option('--force', '-f', is_flag=True, help='Forzar sin confirmación')
def addons_uninstall(name: str, force: bool):
    """🗑️ Desinstalar un addon"""

    registry = AddonRegistry()

    if not registry.get(name):
        console.print(Panel(
            f"[red]Addon '{name}' no encontrado[/red]",
            style="red"
        ))
        return

    if not force:
        if not Confirm.ask(f"[yellow]¿Desinstalar addon '{name}'?[/yellow]"):
            console.print("Operación cancelada")
            return

    console.print(f"[dim]Desinstalando {name}...[/dim]")

    success = registry.unregister(name)

    if success:
        console.print(f"[green]✅ Addon '{name}' desinstalado[/green]")
    else:
        console.print(f"[red]❌ Error desinstalando '{name}'[/red]")


@addons_group.command('info')
@click.argument('name')
def addons_info(name: str):
    """ℹ️ Ver información de un addon"""

    registry = AddonRegistry()
    addon = registry.get(name)

    if not addon:
        console.print(Panel(
            f"[red]Addon '{name}' no encontrado[/red]",
            style="red"
        ))
        return

    manifest = addon.manifest

    console.print(Panel.fit(
        f"[bold cyan]{manifest.name}[/bold cyan] v{manifest.version}\n\n"
        f"[bold]Descripción:[/bold] {manifest.description}\n"
        f"[bold]Autor:[/bold] {manifest.author}\n"
        f"[bold]Licencia:[/bold] {manifest.license}\n"
        f"[bold]Estado:[/bold] {'✅ Activo' if addon.active else '⏸️ Inactivo'}\n"
        f"[bold]Homepage:[/bold] {manifest.homepage or 'N/A'}",
        title="🔌 Información de Addon",
        style="cyan"
    ))

    # Dependencias
    if manifest.dependencies:
        console.print("\n[bold]Dependencias:[/bold]")
        for dep in manifest.dependencies:
            console.print(f"  • {dep}")

    # Herramientas incluidas
    if manifest.tools:
        console.print("\n[bold]Herramientas:[/bold]")
        for tool in manifest.tools:
            console.print(f"  • {tool}")

    # Comandos
    if manifest.commands:
        console.print("\n[bold]Comandos:[/bold]")
        for cmd in manifest.commands:
            console.print(f"  • {cmd}")


@addons_group.command('stats')
def addons_stats():
    """📊 Ver estadísticas de addons"""

    registry = AddonRegistry()
    stats = registry.get_stats()

    console.print(Panel.fit(
        f"[bold]Total addons:[/bold] {stats['total_addons']}\n"
        f"[bold]Activos:[/bold] {stats['active_addons']}\n"
        f"[bold]Inactivos:[/bold] {stats['inactive_addons']}",
        title="📊 Estadísticas de Addons",
        style="green"
    ))

    console.print(f"\n[dim]Directorio: {stats['addons_dir']}[/dim]")


@addons_group.command('reload')
@click.option('--all', '-a', is_flag=True, help='Recargar todos los addons')
def addons_reload(all: bool):
    """🔄 Recargar addons (detecta cambios)"""

    loader = AddonLoader()
    loader.watch_directory(loader.registry._addons_dir)

    console.print("[dim]Buscando cambios...[/dim]")

    changed = loader.check_for_changes()

    if not changed:
        console.print("[green]✅ No hay cambios detectados[/green]")
        return

    console.print(f"\n[yellow]Cambios detectados:[/yellow] {', '.join(changed)}")

    loaded = loader.load_new_addons()
    console.print(f"\n[green]✅ {loaded} addon(s) recargado(s)[/green]")


# Registrar el grupo de comandos
if __name__ == '__main__':
    addons_group()