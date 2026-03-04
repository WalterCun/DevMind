# devmind-core/cli/commands/code.py
"""
Comando de generación de código asistida por IA.

Genera código, modelos, APIs, componentes UI, etc.
con validación y tests incluidos.
"""

import asyncio

import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from rich.syntax import Syntax

from cli.context import ContextManager
from core.config.manager import ConfigManager
from core.orchestrator import DevMindOrchestrator

console = Console()


@click.command('code')
@click.argument('description')
@click.option('--project', '-p', 'project_id', required=True, help='ID del proyecto')
@click.option('--file', '-f', 'target_file', help='Archivo específico a crear/modificar')
@click.option('--language', '-l', type=str, help='Lenguaje de programación (auto-detect si no se especifica)')
@click.option('--dry-run', '-d', is_flag=True, help='Mostrar código sin escribir archivos')
@click.option('--with-tests', '-t', is_flag=True, help='Generar tests unitarios automáticamente')
@click.option('--no-confirm', '-y', is_flag=True, help='No pedir confirmación antes de escribir')
def code_command(
        description: str,
        project_id: str,
        target_file: str,
        language: str,
        dry_run: bool,
        with_tests: bool,
        no_confirm: bool
) -> None:
    """
    💻 Generar código con IA.

    Crea o modifica archivos de código basados en descripciones naturales.

    Ejemplos:

        devmind code --project hotel-api "Crea modelo Reservation con campos user, hotel, check_in, check_out"
        devmind code -p my-app -f models.py "Agrega campo 'status' al modelo User"
        devmind code -p my-app --with-tests "Crea endpoint POST /reservas"
        devmind code -p my-app --dry-run "Función para calcular IVA"
    """
    config_manager = ConfigManager()

    if not config_manager.is_initialized():
        console.print(Panel("❌ Ejecuta: devmind init", style="red"))
        return

    config = config_manager.get_config()

    console.print(Panel.fit(
        f"💻 Generando código para: [bold]{project_id}[/bold]\n"
        f"📝 Solicitud: {description[:80]}{'...' if len(description) > 80 else ''}",
        style="green"
    ))
    console.print()

    # Inicializar contexto y orchestrator
    context_manager = ContextManager()
    session = context_manager.get_or_create_session(project_id=project_id, mode='code')

    orchestrator = DevMindOrchestrator(
        project_id=project_id,
        config=config
    )

    if not orchestrator.initialize():
        console.print("[red]❌ Error inicializando orchestrator[/red]")
        return

    # Construir prompt de generación de código
    code_prompt = _build_code_prompt(description, target_file, language, with_tests, config)

    # Ejecutar generación
    with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
    ) as progress:
        task = progress.add_task("[green]Generando código...", total=None)

        result = asyncio.run(_execute_code_generation(
            orchestrator,
            context_manager,
            session.session_id,
            code_prompt,
            config.agent_name
        ))

        progress.remove_task(task)

    if result and result.get('response'):
        # Procesar resultado
        _process_code_result(
            result,
            project_id,
            dry_run,
            no_confirm,
            config.sandbox_enabled
        )
    else:
        console.print("[red]❌ No se pudo generar el código[/red]")


def _build_code_prompt(
        description: str,
        target_file: str,
        language: str,
        with_tests: bool,
        config
) -> str:
    """Construye el prompt para generación de código"""
    prompt_parts = [
        "Como desarrollador Senior, genera código para:",
        "",
        f"**Solicitud:** {description}",
        "",
    ]

    if target_file:
        prompt_parts.append(f"**Archivo objetivo:** {target_file}")
        prompt_parts.append("")

    if language:
        prompt_parts.append(f"**Lenguaje:** {language}")
    else:
        prompt_parts.append(f"**Lenguajes disponibles:** {', '.join(config.preferred_languages)}")

    prompt_parts.append("")
    prompt_parts.append("**Requisitos:**")
    prompt_parts.append("- Código limpio, legible y siguiendo mejores prácticas")
    prompt_parts.append("- Type hints completos (si el lenguaje lo soporta)")
    prompt_parts.append("- Manejo adecuado de errores")
    prompt_parts.append("- Comentarios solo donde sea necesario")
    prompt_parts.append("- Sigue la estructura del proyecto existente")

    if with_tests:
        prompt_parts.append("- **Incluir tests unitarios** para el código generado")

    prompt_parts.append("")
    prompt_parts.append("**Formato de salida:**")
    prompt_parts.append("```lenguaje")
    prompt_parts.append("# código aquí")
    prompt_parts.append("```")
    prompt_parts.append("")
    prompt_parts.append("Para cada archivo, incluye:")
    prompt_parts.append("- Ruta completa del archivo")
    prompt_parts.append("- Contenido completo (no solo diffs)")
    prompt_parts.append("- Breve descripción de lo que hace")

    return "\n".join(prompt_parts)


async def _execute_code_generation(
        orchestrator: DevMindOrchestrator,
        context_manager: ContextManager,
        session_id: str,
        prompt: str,
        agent_name: str
) -> dict:
    """Ejecuta la generación de código"""
    context_manager.add_message("user", prompt, intent="code")

    try:
        result = await orchestrator.process_message(
            message=prompt,
            session_id=session_id
        )

        context_manager.add_message(
            "agent",
            result.get('response', ''),
            intent="code_response",
            metadata={"type": "code_generation"}
        )

        return result

    except Exception as e:
        console.print(f"[red]❌ Error: {str(e)}[/red]")
        return None


def _process_code_result(
        result: dict,
        project_id: str,
        dry_run: bool,
        no_confirm: bool,
        sandbox_enabled: bool
) -> None:
    """Procesa el resultado de la generación de código"""

    response = result.get('response', '')
    files_modified = result.get('files_modified', [])

    # Extraer bloques de código de la respuesta
    code_blocks = _extract_code_blocks(response)

    if not code_blocks:
        console.print("[yellow]⚠️  No se detectaron bloques de código en la respuesta[/yellow]")
        console.print(Markdown(response))
        return

    # Mostrar código generado
    console.print("\n[bold green]✅ Código generado:[/bold green]\n")

    for i, block in enumerate(code_blocks, 1):
        file_path = block.get('path', f'file_{i}')
        language = block.get('language', 'text')
        code = block.get('code', '')
        description = block.get('description', '')

        console.print(f"[bold]📁 {file_path}[/bold]")
        if description:
            console.print(f"[dim]{description}[/dim]")
        console.print()

        # Mostrar código con syntax highlighting
        try:
            syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        except Exception:
            syntax = Syntax(code, "text", theme="monokai", line_numbers=True)

        if dry_run:
            # Solo mostrar, no escribir
            console.print(syntax)
        else:
            # Preguntar confirmación si no se usó --no-confirm
            if not no_confirm:
                write_file = Confirm.ask(
                    f"[yellow]¿Escribir {file_path}?[/yellow]",
                    default=True
                )
            else:
                write_file = True

            if write_file:
                _write_code_file(project_id, file_path, code, language)
            else:
                console.print(f"[yellow]⏭️  Saltando {file_path}[/yellow]")

        console.print()

    if dry_run:
        console.print("[yellow]⚠️  Modo dry-run: ningún archivo fue escrito[/yellow]")
        console.print("[dim]Usa sin --dry-run para escribir los archivos[/dim]")
    else:
        console.print("[green]✅ Código procesado[/green]")

    # Mostrar tests si se generaron
    if result.get('tests_generated'):
        console.print("\n[bold]🧪 Tests generados:[/bold]")
        for test_file in result['tests_generated']:
            console.print(f"  • {test_file}")


def _extract_code_blocks(response: str) -> list:
    """Extrae bloques de código de la respuesta del agente"""
    import re

    blocks = []

    # Patrón para bloques de código markdown: ```lenguaje\ncontenido```
    pattern = r'```(\w+)?\s*\n(.*?)```'
    matches = re.findall(pattern, response, re.DOTALL)

    for match in matches:
        language = match[0].strip() if match[0] else 'text'
        code_content = match[1].strip()

        # Valores por defecto
        file_path = f'generated_{len(blocks) + 1}.{language}'
        description = ''

        # Intentar extraer ruta: buscar "# ruta:", "# file:", "# path:" al inicio
        # Patrón más flexible: permite espacios, tabs, y captura hasta fin de línea
        route_patterns = [
            r'#\s*ruta\s*:\s*([^\n]+)',
            r'#\s*file\s*:\s*([^\n]+)',
            r'#\s*path\s*:\s*([^\n]+)',
            r'//\s*ruta\s*:\s*([^\n]+)',  # Para JS/TS
            r'//\s*file\s*:\s*([^\n]+)',
        ]

        for route_pattern in route_patterns:
            route_match = re.search(route_pattern, code_content, re.IGNORECASE)
            if route_match:
                file_path = route_match.group(1).strip()
                # Remover la línea de ruta del código para que quede limpio
                code_content = re.sub(route_pattern, '', code_content, flags=re.IGNORECASE).strip()
                break

        # Buscar descripción en la primera línea si es comentario y no es ruta
        first_line = code_content.split('\n')[0].strip() if code_content else ''
        if first_line.startswith('#') or first_line.startswith('//'):
            # Extraer texto después del # o //
            desc_match = re.match(r'^(?:#|//)\s*(.+)$', first_line)
            if desc_match:
                desc_text = desc_match.group(1).strip()
                # Solo usar como descripción si no parece una ruta
                if not any(kw in desc_text.lower() for kw in ['ruta:', 'file:', 'path:', '.py', '.js', '.ts']):
                    description = desc_text

        # Si el código contiene múltiples secciones con rutas, dividirlas
        if re.search(r'(?:#|//)\s*(?:ruta|file|path)\s*:', code_content, re.IGNORECASE):
            # Dividir por líneas que comienzan con comentario de ruta
            sub_sections = re.split(r'(?=(?:#|//)\s*(?:ruta|file|path)\s*:)', code_content)
            for section in sub_sections:
                section = section.strip()
                if not section:
                    continue

                # Extraer ruta de esta sección
                sub_path = file_path  # default
                for route_pattern in route_patterns:
                    sub_match = re.search(route_pattern, section, re.IGNORECASE)
                    if sub_match:
                        sub_path = sub_match.group(1).strip()
                        section = re.sub(route_pattern, '', section, flags=re.IGNORECASE).strip()
                        break

                blocks.append({
                    'path': sub_path,
                    'language': language,
                    'code': section,
                    'description': f'Archivo: {sub_path}'
                })
        else:
            # Bloque único
            blocks.append({
                'path': file_path,
                'language': language,
                'code': code_content,
                'description': description
            })

    # Fallback: si no se encontraron bloques markdown, retornar todo como texto
    if not blocks and response.strip():
        blocks.append({
            'path': 'generated_1.txt',
            'language': 'text',
            'code': response.strip(),
            'description': 'Contenido generado'
        })

    return blocks


def _write_code_file(project_id: str, file_path: str, code: str, language: str) -> bool:
    """Escribe código en un archivo del proyecto"""
    from core.config.manager import ConfigManager

    config_manager = ConfigManager()
    projects_dir = config_manager.CONFIG_DIR / "projects" / project_id

    # Crear directorio si no existe
    full_path = projects_dir / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(code)

        console.print(f"[green]✅ Escrito:[/green] {full_path}")
        return True

    except Exception as e:
        console.print(f"[red]❌ Error escribiendo {file_path}: {str(e)}[/red]")
        return False