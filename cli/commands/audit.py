# devmind-core/cli/commands/audit.py
"""
Comandos CLI para visualización de auditoría de seguridad.
"""

from datetime import datetime, timedelta

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from core.security.auditor import SecurityAuditor, AuditCategory, AuditStatus

console = Console()


@click.group('audit')
def audit_group():
    """📋 Visualización de logs de auditoría"""
    pass


@audit_group.command('view')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--limit', '-l', type=int, default=20, help='Número de eventos a mostrar')
@click.option('--category', '-c', type=click.Choice([c.name for c in AuditCategory]), help='Filtrar por categoría')
@click.option('--status', '-s', type=click.Choice([st.name for st in AuditStatus]), help='Filtrar por estado')
@click.option('--min-risk', '-r', type=float, default=0.0, help='Filtrar por riesgo mínimo')
def audit_view(project_id: str, limit: int, category: str, status: str, min_risk: float):
    """👁️ Ver eventos de auditoría recientes"""

    auditor = SecurityAuditor(project_id=project_id)

    # Convertir strings a enums
    category_enum = AuditCategory[category] if category else None
    status_enum = AuditStatus[status] if status else None

    entries = auditor.get_entries(
        category=category_enum,
        status=status_enum,
        min_risk_score=min_risk,
        limit=limit
    )

    if not entries:
        console.print(Panel(
            "[yellow]No se encontraron eventos de auditoría[/yellow]\n"
            "Intenta ajustar los filtros o verificar el ID del proyecto",
            style="yellow"
        ))
        return

    # Crear tabla
    table = Table(title=f"📋 Auditoría: {project_id}", show_lines=True)
    table.add_column("⏰ Tiempo", style="dim", width=19)
    table.add_column("📁 Categoría", style="cyan", width=15)
    table.add_column("🔧 Acción", style="green", width=20)
    table.add_column("🚦 Estado", width=12)
    table.add_column("⚠️ Riesgo", width=8)
    table.add_column("🤖 Agente", style="magenta")

    for entry in entries:
        risk_color = "green" if entry.risk_score < 0.3 else "yellow" if entry.risk_score < 0.7 else "red"

        table.add_row(
            entry.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            entry.category.name,
            entry.action,
            entry.status.name,
            f"[{risk_color}]{entry.risk_score:.2f}[/{risk_color}]",
            entry.agent_name
        )

    console.print(table)
    console.print(f"\n[dim]Mostrando {len(entries)} de {limit} eventos[/dim]")


@audit_group.command('summary')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--hours', '-h', type=int, default=24, help='Período en horas')
def audit_summary(project_id: str, hours: int):
    """📊 Ver resumen de auditoría"""

    auditor = SecurityAuditor(project_id=project_id)

    start_time = datetime.now() - timedelta(hours=hours)
    summary = auditor.get_summary(start_time=start_time)

    # Panel de resumen
    console.print(Panel(
        f"[bold]Período:[/bold] Últimas {hours} horas\n"
        f"[bold]Total eventos:[/bold] {summary.total_events}\n"
        f"[bold]Riesgo promedio:[/bold] {summary.avg_risk_score:.3f}\n"
        f"[bold]Eventos bloqueados:[/bold] {len(summary.blocked_events)}\n"
        f"[bold]Eventos alto riesgo:[/bold] {len(summary.high_risk_events)}",
        title=f"📊 Resumen de Auditoría: {project_id}",
        style="blue"
    ))
    console.print()

    # Tabla por categoría
    if summary.by_category:
        cat_table = Table(title="Eventos por Categoría")
        cat_table.add_column("Categoría", style="cyan")
        cat_table.add_column("Cantidad", style="green")

        for cat, count in sorted(summary.by_category.items(), key=lambda x: x[1], reverse=True):
            cat_table.add_row(cat, str(count))

        console.print(cat_table)
        console.print()

    # Tabla por estado
    if summary.by_status:
        status_table = Table(title="Eventos por Estado")
        status_table.add_column("Estado", style="cyan")
        status_table.add_column("Cantidad", style="green")

        for st, count in summary.by_status.items():
            status_color = "green" if st == "ALLOWED" else "red" if st == "BLOCKED" else "yellow"
            status_table.add_row(f"[{status_color}]{st}[/{status_color}]", str(count))

        console.print(status_table)


@audit_group.command('risk')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
def audit_risk(project_id: str):
    """⚠️ Evaluación de riesgo del proyecto"""

    auditor = SecurityAuditor(project_id=project_id)
    assessment = auditor.get_risk_assessment()

    risk_color = {
        "CRITICAL": "red",
        "HIGH": "orange",
        "MEDIUM": "yellow",
        "LOW": "blue",
        "MINIMAL": "green"
    }.get(assessment["risk_level"], "white")

    console.print(Panel(
        f"\n[bold {risk_color}]Nivel de Riesgo: {assessment['risk_level']}[/bold {risk_color}]\n\n"
        f"Puntuación: {assessment['risk_score']:.3f}\n\n"
        f"{assessment['assessment']}\n",
        title="⚠️ Evaluación de Riesgo",
        style=risk_color
    ))

    # Recomendaciones
    if assessment.get("recommendations"):
        console.print("\n[bold]💡 Recomendaciones:[/bold]")
        for rec in assessment["recommendations"]:
            console.print(f"  • {rec}")

    # Métricas
    if "metrics" in assessment:
        console.print("\n[bold]📈 Métricas (24h):[/bold]")
        metrics = assessment["metrics"]
        console.print(f"  • Total eventos: {metrics.get('total_events_24h', 0)}")
        console.print(f"  • Eventos bloqueados: {metrics.get('blocked_events', 0)}")
        console.print(f"  • Eventos alto riesgo: {metrics.get('high_risk_events', 0)}")


@audit_group.command('export')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--output', '-o', type=str, default='audit_report.json', help='Archivo de salida')
@click.option('--format', '-f', type=click.Choice(['json', 'csv']), default='json', help='Formato de exportación')
@click.option('--hours', '-h', type=int, default=24, help='Período en horas')
def audit_export(project_id: str, output: str, format: str, hours: int):
    """💾 Exportar reporte de auditoría"""

    auditor = SecurityAuditor(project_id=project_id)
    start_time = datetime.now() - timedelta(hours=hours)

    console.print(f"[dim]Exportando auditoría a {output}...[/dim]")

    success = auditor.export_report(
        output_path=output,
        format=format,
        start_time=start_time
    )

    if success:
        console.print(f"[green]✅ Reporte exportado exitosamente[/green]")
        console.print(f"📁 Archivo: {output}")
    else:
        console.print(f"[red]❌ Error exportando reporte[/red]")


@audit_group.command('clear')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--force', '-f', is_flag=True, help='No pedir confirmación')
def audit_clear(project_id: str, force: bool):
    """🗑️ Limpiar logs de auditoría en memoria"""
    from rich.prompt import Confirm

    if not force:
        if not Confirm.ask(
                "[yellow]¿Limpiar todos los logs de auditoría en memoria?[/yellow]\n[dim]Esto no elimina los archivos guardados[/dim]"):
            console.print("Operación cancelada")
            return

    auditor = SecurityAuditor(project_id=project_id)
    cleared = auditor.clear_entries()

    console.print(f"[green]✅ {cleared} entradas eliminadas de memoria[/green]")


# Registrar el grupo de comandos
if __name__ == '__main__':
    audit_group()