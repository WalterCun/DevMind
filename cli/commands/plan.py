# devmind-core/cli/commands/plan.py
"""
Comando de planificación asistida por IA.

Ayuda a dividir proyectos en fases, estimar tiempos,
identificar riesgos y definir entregables.
"""

import asyncio
import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.tree import Tree
from rich.markdown import Markdown
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator
from cli.context import ContextManager
from cli.streaming import stream_agent_response

console = Console()


@click.command('plan')
@click.argument('description', required=False)
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--phases', '-n', type=int, default=4, help='Número de fases sugeridas (3-8)')
@click.option('--output', '-o', type=click.Choice(['table', 'tree', 'markdown', 'json']), default='table')
@click.option('--interactive', '-i', is_flag=True, help='Modo interactivo con preguntas de refinamiento')
def plan_command(
        description: str,
        project_id: str,
        phases: int,
        output: str,
        interactive: bool
) -> None:
    """
    📋 Planificar proyecto con ayuda de IA.

    Divide tu proyecto en fases estimadas con entregables claros.

    Ejemplos:

        devmind plan --project hotel-api "API REST para gestión de reservas"
        devmind plan -p my-app -n 5 --output tree
        devmind plan -p my-app --interactive
    """
    config_manager = ConfigManager()

    if not config_manager.is_initialized():
        console.print(Panel("❌ Ejecuta: devmind init", style="red"))
        return

    config = config_manager.get_config()

    # Validar número de fases
    phases = max(3, min(8, phases))

    # Si no hay descripción, modo interactivo
    if not description:
        description = _interactive_description(project_id, phases)
        if not description:
            return

    console.print(Panel.fit(
        f"📋 Planificando: [bold]{project_id}[/bold]\n"
        f"📝 Descripción: {description[:100]}{'...' if len(description) > 100 else ''}\n"
        f"🔢 Fases objetivo: {phases}",
        style="cyan"
    ))
    console.print()

    # Inicializar contexto y orchestrator
    context_manager = ContextManager()
    session = context_manager.get_or_create_session(project_id=project_id, mode='plan')

    orchestrator = DevMindOrchestrator(
        project_id=project_id,
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando orchestrator[/red]")
        return

    # Construir prompt de planificación
    planning_prompt = _build_planning_prompt(description, phases, config)

    # Ejecutar planificación
    console.print("[dim]🤖 Analizando y generando plan...[/dim]\n")

    result = asyncio.run(_execute_planning(
        orchestrator,
        context_manager,
        session.session_id,
        planning_prompt,
        config.agent_name
    ))

    if result and result.get('response'):
        # Mostrar resultado en formato seleccionado
        _display_plan(result['response'], output)

        # Guardar plan en memoria del proyecto
        _save_plan_to_memory(orchestrator, project_id, result['response'])

        console.print("\n[green]✅ Plan generado y guardado[/green]")
        console.print("[dim]💡 Usa 'devmind code' para comenzar a implementar la Fase 1[/dim]")
    else:
        console.print("[red]❌ No se pudo generar el plan[/red]")


def _interactive_description(project_id: str, phases: int) -> str:
    """Modo interactivo para obtener descripción del proyecto"""
    console.print(Panel(
        "[bold]📋 Asistente de Planificación Interactiva[/bold]\n\n"
        "Te haré algunas preguntas para entender mejor tu proyecto.",
        style="cyan"
    ))
    console.print()

    # Pregunta 1: Descripción general
    description = console.input(
        "[bold]1️⃣  Descripción del proyecto:[/bold] "
    ).strip()

    if not description:
        console.print("[yellow]⚠️  Descripción requerida[/yellow]")
        return ""

    # Pregunta 2: Stack tecnológico
    stack = console.input(
        "[bold]2️⃣  Stack tecnológico (opcional):[/bold] "
    ).strip()

    if stack:
        description += f"\n\nStack: {stack}"

    # Pregunta 3: Restricciones
    constraints = console.input(
        "[bold]3️⃣  Restricciones o requisitos especiales (opcional):[/bold] "
    ).strip()

    if constraints:
        description += f"\n\nRestricciones: {constraints}"

    # Pregunta 4: Criterios de éxito
    success = console.input(
        "[bold]4️⃣  Criterios de éxito (opcional):[/bold] "
    ).strip()

    if success:
        description += f"\n\nÉxito: {success}"

    return description


def _build_planning_prompt(description: str, phases: int, config) -> str:
    """Construye el prompt para el agente de planificación"""
    return f"""Como Director de Proyecto experto, crea un plan detallado con {phases} fases para:

{description}

Configuración del equipo:
- Lenguajes conocidos: {', '.join(config.preferred_languages)}
- Modo de autonomía: {config.autonomy_mode}

El plan debe incluir para cada fase:
1. Nombre y objetivo de la fase
2. Duración estimada (en horas)
3. Entregables concretos (archivos, componentes, features)
4. Dependencias con otras fases
5. Riesgos potenciales y mitigaciones
6. Criterios de aceptación

Formato de salida esperado (JSON):
{{
    "project_name": "...",
    "total_estimated_hours": 0,
    "phases": [
        {{
            "number": 1,
            "name": "...",
            "objective": "...",
            "estimated_hours": 0,
            "deliverables": ["...", "..."],
            "dependencies": [],
            "risks": ["..."],
            "acceptance_criteria": ["..."]
        }}
    ],
    "recommendations": ["...", "..."]
}}

Sé realista en las estimaciones. Considera tiempo para testing, documentación y imprevistos."""


async def _execute_planning(
        orchestrator: DevMindOrchestrator,
        context_manager: ContextManager,
        session_id: str,
        prompt: str,
        agent_name: str
) -> dict:
    """Ejecuta la planificación a través del orchestrator"""
    context_manager.add_message("user", prompt, intent="plan")

    try:
        result = await orchestrator.process_message(
            message=prompt,
            session_id=session_id
        )

        context_manager.add_message(
            "agent",
            result.get('response', ''),
            intent="plan_response",
            metadata={"type": "project_plan"}
        )

        return result

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        context_manager.add_message("system", f"Error: {str(e)}")
        return None


def _display_plan(response: str, output_format: str) -> None:
    """Muestra el plan en el formato seleccionado"""
    import json
    from core.utils.helpers import parse_json_safe

    # Intentar parsear JSON de la respuesta
    plan_data = parse_json_safe(response)

    if output_format == 'json':
        # Salida JSON raw
        console.print(json.dumps(plan_data if plan_data else {"raw": response}, indent=2, ensure_ascii=False))
        return

    if output_format == 'markdown':
        # Salida Markdown
        console.print(Markdown(response if not plan_data else _plan_to_markdown(plan_data)))
        return

    if output_format == 'tree':
        # Árbol visual
        _display_plan_tree(plan_data if plan_data else response)
        return

    # Default: tablas
    _display_plan_tables(plan_data if plan_data else response)


def _display_plan_tables(plan_data) -> None:
    """Muestra el plan en formato de tablas"""
    if isinstance(plan_data, str):
        console.print(Markdown(plan_data))
        return

    # Tabla de resumen del proyecto
    summary_table = Table(title="📊 Resumen del Proyecto")
    summary_table.add_column("Métrica", style="cyan")
    summary_table.add_column("Valor", style="green")

    summary_table.add_row("Proyecto", plan_data.get("project_name", "N/A"))
    summary_table.add_row("Fases", str(len(plan_data.get("phases", []))))
    summary_table.add_row("Horas Estimadas", str(plan_data.get("total_estimated_hours", "N/A")))

    console.print(summary_table)
    console.print()

    # Tabla de fases
    phases_table = Table(title="📋 Fases del Proyecto")
    phases_table.add_column("#", style="cyan", width=3)
    phases_table.add_column("Fase", style="green")
    phases_table.add_column("Horas", style="yellow", width=8)
    phases_table.add_column("Entregables", style="dim")

    for phase in plan_data.get("phases", []):
        deliverables = phase.get("deliverables", [])
        deliverables_text = ", ".join(deliverables[:3])
        if len(deliverables) > 3:
            deliverables_text += f" (+{len(deliverables) - 3} más)"

        phases_table.add_row(
            str(phase.get("number", "?")),
            phase.get("name", "Sin nombre"),
            str(phase.get("estimated_hours", "?")),
            deliverables_text
        )

    console.print(phases_table)

    # Recomendaciones
    recommendations = plan_data.get("recommendations", [])
    if recommendations:
        console.print("\n[bold]💡 Recomendaciones:[/bold]")
        for rec in recommendations[:5]:
            console.print(f"  • {rec}")


def _display_plan_tree(plan_data) -> None:
    """Muestra el plan como árbol jerárquico"""
    if isinstance(plan_data, str):
        console.print(Markdown(plan_data))
        return

    tree = Tree(f"📋 {plan_data.get('project_name', 'Proyecto')}")
    tree.add(f"[bold]Horas totales:[/bold] {plan_data.get('total_estimated_hours', 'N/A')}")

    for phase in plan_data.get("phases", []):
        phase_branch = tree.add(
            f"[bold green]Fase {phase.get('number', '?')}: {phase.get('name', 'Sin nombre')}[/bold green]")
        phase_branch.add(f"⏱️  {phase.get('estimated_hours', '?')} horas")

        deliverables = phase.get("deliverables", [])
        if deliverables:
            del_branch = phase_branch.add("📦 Entregables")
            for d in deliverables:
                del_branch.add(d)

        risks = phase.get("risks", [])
        if risks:
            risk_branch = phase_branch.add("⚠️  Riesgos")
            for r in risks:
                risk_branch.add(r)

    console.print(tree)


def _plan_to_markdown(plan_data) -> str:
    """Convierte plan a formato Markdown"""
    if isinstance(plan_data, str):
        return plan_data

    md = [f"# 📋 {plan_data.get('project_name', 'Plan de Proyecto')}\n"]
    md.append(f"**Horas estimadas:** {plan_data.get('total_estimated_hours', 'N/A')}\n")
    md.append(f"**Fases:** {len(plan_data.get('phases', []))}\n")

    md.append("\n## Fases\n")
    for phase in plan_data.get("phases", []):
        md.append(f"\n### Fase {phase.get('number', '?')}: {phase.get('name', 'Sin nombre')}\n")
        md.append(f"- **Objetivo:** {phase.get('objective', 'N/A')}\n")
        md.append(f"- **Duración:** {phase.get('estimated_hours', '?')} horas\n")
        md.append(f"- **Entregables:** {', '.join(phase.get('deliverables', []))}\n")

        if phase.get('risks'):
            md.append(f"- **Riesgos:** {', '.join(phase.get('risks', []))}\n")

    if plan_data.get('recommendations'):
        md.append("\n## Recomendaciones\n")
        for rec in plan_data.get('recommendations', []):
            md.append(f"- {rec}\n")

    return "\n".join(md)


def _save_plan_to_memory(orchestrator: DevMindOrchestrator, project_id: str, plan_response: str) -> None:
    """Guarda el plan en la memoria vectorial del proyecto"""
    try:
        orchestrator.vector_memory.store(
            content=plan_response[:8000],  # Limitar tamaño
            metadata={"type": "project_plan", "project_id": project_id},
            category="requirements"
        )
    except Exception as e:
        console.print(f"[dim]⚠️  No se pudo guardar en memoria: {str(e)}[/dim]")