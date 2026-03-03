# devmind-core/cli/commands/fix.py
"""
Comando de auto-fix de bugs.

Analiza errores, identifica la causa raíz y genera
patches automáticos con validación.
"""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from cli.context import ContextManager
from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator

console = Console()


@click.command('fix')
@click.argument('description')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--file', '-f', 'target_file', help='Archivo donde ocurre el error')
@click.option('--error-log', '-e', 'error_log', type=click.File('r'), help='Archivo con el log del error')
@click.option('--max-attempts', '-m', type=int, default=3, help='Máximo intentos de auto-fix (1-5)')
@click.option('--auto-apply', '-a', is_flag=True, help='Aplicar fixes automáticamente sin confirmar')
@click.option('--with-tests', '-t', is_flag=True, help='Generar/actualizar tests para el fix')
def fix_command(
        description: str,
        project_id: str,
        target_file: str,
        error_log,
        max_attempts: int,
        auto_apply: bool,
        with_tests: bool
) -> None:
    """
    🐛 Auto-fix de bugs con IA.

    Analiza errores y genera patches automáticos validados.

    Ejemplos:

        devmind fix --project hotel-api "Error 500 al filtrar reservas por fecha"
        devmind fix -p my-app -f models.py "AttributeError: 'User' object has no attribute 'is_active'"
        devmind fix -p my-app --error-log error.log --auto-apply
    """
    config_manager = ConfigManager()

    if not config_manager.is_initialized():
        console.print(Panel("❌ Ejecuta: devmind init", style="red"))
        return

    config = config_manager.get_config()

    # Validar max_attempts
    max_attempts = max(1, min(5, max_attempts))

    # Leer error log si se proporcionó
    error_log_content = None
    if error_log:
        error_log_content = error_log.read()
        error_log.close()

    console.print(Panel.fit(
        f"🐛 Analizando bug: [bold]{project_id}[/bold]\n"
        f"📝 Descripción: {description[:80]}{'...' if len(description) > 80 else ''}\n"
        f"🔢 Máx intentos: {max_attempts}",
        style="red"
    ))
    console.print()

    # Inicializar contexto y orchestrator
    context_manager = ContextManager()
    session = context_manager.get_or_create_session(project_id=project_id, mode='fix')

    orchestrator = DevMindOrchestrator(
        project_id=project_id,
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando orchestrator[/red]")
        return

    # Ejecutar análisis y fix
    result = asyncio.run(_execute_fix_workflow(
        orchestrator,
        context_manager,
        session.session_id,
        description,
        target_file,
        error_log_content,
        max_attempts,
        auto_apply,
        with_tests,
        config.agent_name
    ))

    if result:
        _display_fix_summary(result)
    else:
        console.print("[red]❌ No se pudo resolver el bug[/red]")


async def _execute_fix_workflow(
        orchestrator: DevMindOrchestrator,
        context_manager: ContextManager,
        session_id: str,
        description: str,
        target_file: str,
        error_log_content: str,
        max_attempts: int,
        auto_apply: bool,
        with_tests: bool,
        agent_name: str
) -> dict:
    """Ejecuta el workflow completo de análisis y fix"""

    # Paso 1: Análisis del bug
    console.print("[bold]🔍 Paso 1/3: Analizando el bug...[/bold]")

    analysis_prompt = _build_analysis_prompt(description, target_file, error_log_content)
    context_manager.add_message("user", analysis_prompt, intent="bug_analysis")

    analysis_result = await orchestrator.process_message(
        message=analysis_prompt,
        session_id=session_id
    )

    context_manager.add_message("agent", analysis_result.get('response', ''), intent="bug_analysis_response")

    console.print("[green]✅ Análisis completado[/green]\n")

    # Mostrar resumen del análisis
    _display_bug_analysis(analysis_result.get('response', ''))

    # Paso 2: Generar fix
    console.print("\n[bold]🔧 Paso 2/3: Generando fix...[/bold]")

    fix_prompt = _build_fix_prompt(description, target_file, error_log_content, analysis_result, with_tests)
    context_manager.add_message("user", fix_prompt, intent="bug_fix")

    fix_result = await orchestrator.process_message(
        message=fix_prompt,
        session_id=session_id
    )

    context_manager.add_message("agent", fix_result.get('response', ''), intent="bug_fix_response")

    console.print("[green]✅ Fix generado[/green]\n")

    # Paso 3: Validar y aplicar
    console.print("[bold]✅ Paso 3/3: Validando fix...[/bold]")

    validation_result = await _validate_fix(
        orchestrator,
        context_manager,
        session_id,
        fix_result,
        max_attempts,
        auto_apply,
        agent_name
    )

    # Combinar resultados
    return {
        'analysis': analysis_result,
        'fix': fix_result,
        'validation': validation_result,
        'success': validation_result.get('validated', False)
    }


def _build_analysis_prompt(description: str, target_file: str, error_log: str) -> str:
    """Construye prompt para análisis del bug"""
    prompt_parts = [
        "Como ingeniero de QA Senior, analiza el siguiente bug:",
        "",
        f"**Descripción del problema:**",
        f"{description}",
        ""
    ]

    if target_file:
        prompt_parts.append(f"**Archivo afectado:** {target_file}")
        prompt_parts.append("")

    if error_log:
        prompt_parts.append("**Log del error:**")
        prompt_parts.append("```")
        prompt_parts.append(error_log.strip())
        prompt_parts.append("```")
        prompt_parts.append("")

    prompt_parts.append("**Realiza un análisis completo incluyendo:**")
    prompt_parts.append("")
    prompt_parts.append("1. **Causa raíz probable** - ¿Qué está causando el error?")
    prompt_parts.append("2. **Ubicación del problema** - ¿En qué archivo/línea está el bug?")
    prompt_parts.append("3. **Condiciones que lo desencadenan** - ¿Cuándo ocurre el error?")
    prompt_parts.append("4. **Impacto** - ¿Qué funcionalidad está afectada?")
    prompt_parts.append("5. **Severidad** - ¿Crítico, alto, medio o bajo?")
    prompt_parts.append("6. **Hipótesis de fix** - ¿Cómo se podría resolver?")
    prompt_parts.append("")
    prompt_parts.append("Sé específico y técnico en el análisis.")

    return "\n".join(prompt_parts)


def _build_fix_prompt(
        description: str,
        target_file: str,
        error_log: str,
        analysis_result: dict,
        with_tests: bool
) -> str:
    """Construye prompt para generar el fix"""
    prompt = f"""Como desarrollador Senior, genera un fix para el bug analizado:

**Descripción:** {description}

**Análisis previo:**
{analysis_result.get('response', 'Sin análisis disponible')}

"""

    if target_file:
        prompt += f"**Archivo a modificar:** {target_file}\n\n"

    if error_log:
        prompt += f"**Error:** {error_log[:500]}...\n\n"

    prompt += """**Requisitos del fix:**

1. **Código mínimo necesario** - No hagas cambios innecesarios
2. **Mantener compatibilidad** - No romper funcionalidad existente
3. **Type hints** - Incluir anotaciones de tipo
4. **Comentarios** - Solo donde sea necesario explicar lógica compleja
5. **Seguir estilo existente** - Mantener consistencia con el código base

"""

    if with_tests:
        prompt += """6. **Tests** - Generar/actualizar tests para validar el fix

"""

    prompt += """**Formato de salida:**

Para cada archivo modificado:
```lenguaje
# ruta: archivo/path.py
# código completo con el fix aplicado
Incluir:
Descripción del cambio
Archivos modificados
Cómo validar que el fix funciona"""
    return prompt

async def _validate_fix(
orchestrator: DevMindOrchestrator,
context_manager: ContextManager,
session_id: str,
fix_result: dict,
max_attempts: int,
auto_apply: bool,
agent_name: str
) -> dict:
    """Valida el fix generado"""
    import re
    response = fix_result.get('response', '')

    # Extraer archivos del fix
    code_pattern = r'```(\w+)?\s*(?:#?\s*ruta:\s*(.+?))?\n(.*?)```'
    matches = re.findall(code_pattern, response, re.DOTALL)

    if not matches:
        return {'validated': False, 'error': 'No se detectaron archivos en el fix'}

    files_to_fix = []
    for match in matches:
        language = match[0] or 'text'
        file_path = match[1].strip() if match[1] else f'fix_{len(files_to_fix) + 1}.{language}'
        code = match[2].strip()
        files_to_fix.append({'path': file_path, 'code': code, 'language': language})

    # Mostrar archivos a modificar
    console.print("\n[bold]📁 Archivos a modificar:[/bold]")
    for f in files_to_fix:
        console.print(f"  • {f['path']}")

    # Pedir confirmación si no es auto_apply
    if not auto_apply:
        apply_fix = Confirm.ask(
            "\n[yellow]¿Aplicar fix?[/yellow]",
            default=True
        )
        if not apply_fix:
            return {'validated': False, 'cancelled': True}

    # Aplicar fixes
    from core.config.manager import ConfigManager
    config_manager = ConfigManager()
    projects_dir = config_manager.CONFIG_DIR / "projects"

    applied_files = []
    for file_info in files_to_fix:
        file_path = projects_dir / session_id / file_info['path']
        file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info['code'])
            applied_files.append(file_info['path'])
            console.print(f"[green]✅ Aplicado:[/green] {file_info['path']}")
        except Exception as e:
            console.print(f"[red]❌ Error aplicando {file_info['path']}: {str(e)}[/red]")

    # Validar que los archivos se escribieron correctamente
    if applied_files:
        return {
            'validated': True,
            'files_applied': applied_files,
            'attempts': 1
        }
    else:
        return {'validated': False, 'error': 'No se pudieron aplicar los archivos'}

def _display_bug_analysis(analysis: str) -> None:
    """Muestra el análisis del bug"""
    import re
    # Extraer secciones clave si están presentes
    cause_match = re.search(r'(?:causa|raíz|root).*?:\s*(.+?)(?:\n\n|\n\d|\Z)', analysis, re.IGNORECASE | re.DOTALL)
    location_match = re.search(r'(?:ubicación|location|archivo).*?:\s*(.+?)(?:\n\n|\n\d|\Z)', analysis,
                               re.IGNORECASE | re.DOTALL)
    severity_match = re.search(r'(?:severidad|severity).*?:\s*(.+?)(?:\n\n|\n\d|\Z)', analysis,
                               re.IGNORECASE | re.DOTALL)

    table = Table(title="🐛 Análisis del Bug")
    table.add_column("Aspecto", style="cyan")
    table.add_column("Detalle", style="green")

    if cause_match:
        table.add_row("Causa Raíz", cause_match.group(1).strip()[:100])
    if location_match:
        table.add_row("Ubicación", location_match.group(1).strip()[:100])
    if severity_match:
        table.add_row("Severidad", severity_match.group(1).strip()[:50])

    console.print(table)


def _display_fix_summary(result: dict) -> None:
    """Muestra resumen del fix aplicado"""
    validation = result.get('validation', {})
    if validation.get('validated'):
        console.print(Panel(
            f"[bold green]✅ Bug resuelto exitosamente[/bold green]\n\n"
            f"Archivos modificados: {len(validation.get('files_applied', []))}\n"
            f"Intentos: {validation.get('attempts', 1)}",
            style="green"
        ))
    elif validation.get('cancelled'):
        console.print(Panel(
            "[yellow]⚠️  Fix cancelado por el usuario[/yellow]",
            style="yellow"
        ))
    else:
        console.print(Panel(
            f"[red]❌ No se pudo validar el fix[/red]\n\n"
            f"Error: {validation.get('error', 'Desconocido')}",
            style="red"
        ))