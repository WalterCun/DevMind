# devmind-core/cli/commands/tools.py
"""
Comandos CLI para gestión de herramientas.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree

from core.tools.registry import ToolRegistry

console = Console()


@click.group('tools')
def tools_group():
    """🛠️ Gestión de herramientas del sistema"""
    pass


@tools_group.command('list')
@click.option('--category', '-c', type=str, help='Filtrar por categoría')
@click.option('--author', '-a', type=str, help='Filtrar por autor')
@click.option('--format', '-f', type=click.Choice(['table', 'json']), default='table')
def tools_list(category: str, author: str, format: str):
    """📋 Listar herramientas disponibles"""

    registry = ToolRegistry()
    tools = registry.list_tools(category=category, author=author)

    if not tools:
        console.print(Panel(
            "[yellow]No se encontraron herramientas[/yellow]\n"
            "Usa 'devmind tools search' para buscar por texto",
            style="yellow"
        ))
        return

    if format == 'json':
        import json
        console.print(json.dumps(tools, indent=2, ensure_ascii=False))
        return

    # Formato tabla
    table = Table(title=f"🛠️ Herramientas ({len(tools)})")
    table.add_column("Nombre", style="cyan", width=25)
    table.add_column("Categoría", style="green", width=12)
    table.add_column("Autor", width=10)
    table.add_column("Ejecuciones", justify="right")
    table.add_column("Descripción", style="dim")

    for tool in tools:
        definition = tool.get("definition", {})
        stats = tool.get("stats", {})

        table.add_row(
            definition.get("name", "Unknown"),
            definition.get("category", "custom"),
            definition.get("author", "system"),
            str(stats.get("execution_count", 0)),
            definition.get("description", "")[:50] + "..."
        )

    console.print(table)


@tools_group.command('search')
@click.argument('query')
@click.option('--limit', '-l', type=int, default=10, help='Máximo resultados')
def tools_search(query: str, limit: int):
    """🔍 Buscar herramientas por texto"""

    registry = ToolRegistry()
    results = registry.search(query)

    if not results:
        console.print(Panel(
            f"[yellow]No se encontraron herramientas para '{query}'[/yellow]",
            style="yellow"
        ))
        return

    console.print(f"\n[bold]Resultados para '{query}':[/bold] {len(results)} encontrados\n")

    for i, tool in enumerate(results[:limit], 1):
        definition = tool.get("definition", {})

        tree = Tree(f"[cyan]{i}. {definition.get('name')}[/cyan]")
        tree.add(f"[green]Categoría:[/green] {definition.get('category')}")
        tree.add(f"[green]Descripción:[/green] {definition.get('description')}")
        tree.add(f"[green]Tags:[/green] {', '.join(definition.get('tags', []))}")
        tree.add(f"[green]Autor:[/green] {definition.get('author')}")

        console.print(tree)
        console.print()


@tools_group.command('info')
@click.argument('name')
def tools_info(name: str):
    """ℹ️ Ver información detallada de una herramienta"""

    registry = ToolRegistry()
    tool = registry.get(name)

    if not tool:
        console.print(Panel(
            f"[red]Herramienta '{name}' no encontrada[/red]",
            style="red"
        ))
        return

    definition = tool.definition

    console.print(Panel.fit(
        f"[bold cyan]{definition.name}[/bold cyan]\n\n"
        f"[bold]Descripción:[/bold] {definition.description}\n"
        f"[bold]Categoría:[/bold] {definition.category}\n"
        f"[bold]Autor:[/bold] {definition.author}\n"
        f"[bold]Versión:[/bold] {definition.version}\n"
        f"[bold]Tags:[/bold] {', '.join(definition.tags)}",
        title="🛠️ Información de Herramienta",
        style="cyan"
    ))

    # Parámetros
    if definition.parameters:
        console.print("\n[bold]Parámetros:[/bold]")
        for param in definition.parameters:
            required = "[red]*[/red]" if param.required else ""
            console.print(f"  {required} [green]{param.name}[/green] ({param.type}): {param.description}")
            if param.default is not None:
                console.print(f"      Default: {param.default}")

    # Ejemplos
    if definition.examples:
        console.print("\n[bold]Ejemplos:[/bold]")
        for example in definition.examples:
            console.print(f"  • {example}")

    # Estadísticas
    stats = tool.get_stats()
    console.print("\n[bold]Estadísticas:[/bold]")
    console.print(f"  Ejecuciones: {stats.get('execution_count', 0)}")
    console.print(f"  Tiempo promedio: {stats.get('avg_execution_time', 0):.3f}s")


@tools_group.command('stats')
def tools_stats():
    """📊 Ver estadísticas de uso de herramientas"""

    registry = ToolRegistry()
    stats = registry.get_stats()

    console.print(Panel.fit(
        f"[bold]Total herramientas:[/bold] {stats['total_tools']}\n"
        f"[bold]Total ejecuciones:[/bold] {stats['total_executions']}\n"
        f"[bold]Auto-generadas:[/bold] {stats['auto_generated']}",
        title="📊 Estadísticas de Herramientas",
        style="green"
    ))

    # Por categoría
    if stats['by_category']:
        console.print("\n[bold]Por categoría:[/bold]")
        for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
            console.print(f"  {cat}: {count}")

    # Por autor
    if stats['by_author']:
        console.print("\n[bold]Por autor:[/bold]")
        for author, count in sorted(stats['by_author'].items(), key=lambda x: x[1], reverse=True):
            console.print(f"  {author}: {count}")


@tools_group.command('execute')
@click.argument('name')
@click.option('--param', '-p', 'params', multiple=True, help='Parámetro en formato key=value')
@click.option('--json', '-j', 'json_input', type=str, help='Parámetros en formato JSON')
def tools_execute(name: str, params: tuple, json_input: str):
    """⚡ Ejecutar una herramienta manualmente"""

    registry = ToolRegistry()

    # Parsear parámetros
    kwargs = {}

    if json_input:
        import json
        try:
            kwargs = json.loads(json_input)
        except json.JSONDecodeError as e:
            console.print(f"[red]Error parsing JSON: {e}[/red]")
            return

    for param in params:
        if '=' in param:
            key, value = param.split('=', 1)
            kwargs[key] = value

    # Ejecutar
    console.print(f"[dim]Ejecutando {name}...[/dim]\n")

    result = registry.execute(name, **kwargs)

    if result.success:
        console.print("[green]✅ Ejecución exitosa[/green]")
        console.print(f"\n[bold]Output:[/bold]")
        console.print(result.output)
        console.print(f"\n[dim]Tiempo: {result.execution_time:.3f}s[/dim]")
    else:
        console.print("[red]❌ Ejecución fallida[/red]")
        console.print(f"[red]Error: {result.error}[/red]")


# Registrar el grupo de comandos
if __name__ == '__main__':
    tools_group()