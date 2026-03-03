# devmind-core/cli/commands/sandbox.py
"""
Comandos CLI para gestión de sandbox de seguridad.
"""

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Confirm

from core.security.sandbox import ExecutionSandbox, SandboxConfig, SandboxStatus

console = Console()


@click.group('sandbox')
def sandbox_group():
    """🛡️ Gestión de sandbox de ejecución segura"""
    pass


@sandbox_group.command('test')
@click.argument('code')
@click.option('--timeout', '-t', type=int, default=30, help='Timeout en segundos')
@click.option('--memory', '-m', type=str, default='256m', help='Límite de memoria')
@click.option('--network', '-n', is_flag=True, help='Habilitar acceso a red')
def sandbox_test(code: str, timeout: int, memory: str, network: bool):
    """
    🔬 Probar código en sandbox aislado.

    Ejecuta un fragmento de código Python en un entorno seguro
    y muestra el resultado.

    Ejemplo:

        devmind sandbox test "print('Hello World')"
        devmind sandbox test "import os; print(os.getcwd())" --network
    """
    console.print(Panel.fit(
        f"🔬 Ejecutando en sandbox seguro\n"
        f"⏱️  Timeout: {timeout}s | 💾 Memoria: {memory}",
        style="cyan"
    ))
    console.print()

    config = SandboxConfig(
        timeout_seconds=timeout,
        memory_limit=memory,
        network_enabled=network
    )

    import asyncio

    async def run_test():
        async with ExecutionSandbox(project_id="cli_test", config=config) as sandbox:
            console.print("[dim]Ejecutando código...[/dim]\n")

            result = await sandbox.execute_python(code)

            if result.success:
                console.print("[green]✅ Ejecución exitosa[/green]")
                console.print(f"⏱️  Tiempo: {result.execution_time:.2f}s")

                if result.stdout:
                    console.print("\n[bold]STDOUT:[/bold]")
                    console.print(result.stdout)

                if result.stderr:
                    console.print("\n[bold]STDERR:[/bold]")
                    console.print(result.stderr)
            else:
                console.print("[red]❌ Ejecución fallida[/red]")
                console.print(f"Código de salida: {result.exit_code}")
                console.print(f"Error: {result.error}")

                if result.stderr:
                    console.print("\n[bold]STDERR:[/bold]")
                    console.print(result.stderr)

    try:
        asyncio.run(run_test())
    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")


@sandbox_group.command('status')
def sandbox_status():
    """📊 Ver estado del servicio Docker para sandbox"""
    import subprocess

    console.print(Panel.fit("🛡️ Estado del Sandbox", style="blue"))
    console.print()

    # Verificar Docker
    try:
        result = subprocess.run(
            ["docker", "version", "--format", "{{.Server.Version}}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode == 0:
            console.print("[green]✅ Docker:[/green] Disponible")
            console.print(f"   Versión: {result.stdout.strip()}")
        else:
            console.print("[red]❌ Docker:[/red] No disponible")
    except FileNotFoundError:
        console.print("[red]❌ Docker:[/red] No instalado")
    except Exception as e:
        console.print(f"[red]❌ Docker:[/red] Error - {e}")

    console.print()

    # Verificar contenedores activos de DevMind
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", "name=devmind", "--format", "table {{.Names}}\t{{.Status}}"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.stdout.strip():
            console.print("[bold]Contenedores DevMind activos:[/bold]")
            console.print(result.stdout)
        else:
            console.print("[dim]No hay contenedores DevMind activos[/dim]")
    except Exception as e:
        console.print(f"[dim]No se pudo verificar contenedores: {e}[/dim]")


@sandbox_group.command('cleanup')
@click.option('--force', '-f', is_flag=True, help='No pedir confirmación')
def sandbox_cleanup(force: bool):
    """🧹 Limpiar contenedores sandbox huérfanos"""
    import subprocess

    if not force:
        if not Confirm.ask("[yellow]¿Eliminar todos los contenedores sandbox huérfanos?[/yellow]"):
            console.print("Operación cancelada")
            return

    console.print("[dim]Buscando contenedores huérfanos...[/dim]")

    try:
        # Encontrar contenedores con nombre sandbox_*
        result = subprocess.run(
            ["docker", "ps", "-a", "--filter", "name=sandbox_", "--format", "{{.ID}}"],
            capture_output=True,
            text=True,
            timeout=10
        )

        containers = [c.strip() for c in result.stdout.split('\n') if c.strip()]

        if not containers:
            console.print("[green]✅ No hay contenedores huérfanos[/green]")
            return

        console.print(f"Encontrados {len(containers)} contenedores para eliminar:")
        for c in containers:
            console.print(f"  • {c[:12]}")

        # Eliminar contenedores
        for c in containers:
            subprocess.run(
                ["docker", "rm", "-f", c],
                capture_output=True,
                timeout=10
            )

        console.print(f"[green]✅ {len(containers)} contenedores eliminados[/green]")

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")


# Registrar el grupo de comandos
if __name__ == '__main__':
    sandbox_group()