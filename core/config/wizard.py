# devmind-core/core/config/wizard.py
"""
Wizard de configuración inicial de DevMind Core.

Guía interactiva para que el usuario configure la identidad,
capacidades y preferencias del agente autónomo.
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

try:
    import questionary
except ImportError:
    print("⚠️ questionary no instalado. Ejecuta: uv pip install questionary")
    sys.exit(1)

from .schema import (
    AgentConfig,
    PersonalityType,
    AutonomyMode,
    LearningMode,
    AuditFrequency,
    GitConfig,
)


class OnboardingWizard:
    """
    Wizard interactivo para configuración inicial del agente.

    Guía al usuario a través de una serie de preguntas para establecer
    la identidad, capacidades y preferencias del agente DevMind.
    """

    CONFIG_DIR: Path = Path.home() / ".devmind"
    CONFIG_FILE: Path = CONFIG_DIR / "config.json"
    TEMP_FILE: Path = CONFIG_DIR / ".wizard_temp.json"  # ✅ Guardado temporal

    # Definición de pasos del wizard
    STEPS = [
        {
            'id': 'identity',
            'title': '🆔 Identidad del Agente',
            'icon': '🆔',
            'description': 'Define cómo se llamará y comportará tu agente',
            'questions': [
                {
                    'field': 'agent_name',
                    'prompt': '¿Cómo quieres llamar a tu agente?',
                    'type': 'text',
                    'default': 'DevMind',
                    'help': 'Este nombre se usará en todas las interacciones',
                    'validate': lambda x: 1 <= len(x) <= 50
                },
                {
                    'field': 'personality',
                    'prompt': '¿Qué personalidad tendrá?',
                    'type': 'select',
                    'options': [
                        {'name': '👔 Profesional - Formal y directo', 'value': 'professional'},
                        {'name': '😊 Casual - Amigable y relajado', 'value': 'casual'},
                        {'name': '🤓 Técnico - Detallado y preciso', 'value': 'technical'},
                        {'name': '🎓 Mentor - Educativo y paciente', 'value': 'mentor'}
                    ],
                    'default': 'professional'
                },
                {
                    'field': 'communication_style',
                    'prompt': 'Estilo de comunicación',
                    'type': 'select',
                    'options': [
                        {'name': '⚡ Conciso - Respuestas breves y directas', 'value': 'concise'},
                        {'name': '📖 Detallado - Explicaciones completas', 'value': 'detailed'},
                        {'name': '🎓 Educativo - Enseña mientras trabaja', 'value': 'educational'}
                    ],
                    'default': 'concise'
                }
            ]
        },
        {
            'id': 'capabilities',
            'title': '⚡ Capacidades y Permisos',
            'icon': '⚡',
            'description': 'Define qué puede hacer el agente autónomamente',
            'questions': [
                {
                    'field': 'autonomy_mode',
                    'prompt': 'Nivel de autonomía',
                    'type': 'select',
                    'options': [
                        {'name': '🛡️ Supervisado - Pide confirmación para todo', 'value': 'supervised'},
                        {'name': '⚖️ Semi-Autónomo - Autonomía para tareas simples', 'value': 'semi_autonomous'},
                        {'name': '🚀 Full Autónomo - Ejecuta sin preguntar (sandbox)', 'value': 'full_autonomous'}
                    ],
                    'default': 'supervised',
                    'help': 'Puedes cambiar esto después en la configuración'
                },
                {
                    'field': 'max_file_write_without_confirm',
                    'prompt': 'Máximo archivos a escribir sin confirmar',
                    'type': 'number',
                    'default': 5,
                    'min': 1,
                    'max': 50,
                    'help': 'En modo supervisado, límite de archivos antes de pedir confirmación'
                },
                {
                    'field': 'allow_internet',
                    'prompt': '¿Permitir acceso a internet?',
                    'type': 'confirm',
                    'default': False,
                    'help': 'Necesario para descargar documentación o paquetes'
                },
                {
                    'field': 'allow_email',
                    'prompt': '¿Permitir envío/lectura de emails?',
                    'type': 'confirm',
                    'default': False,
                    'help': 'Requiere configuración SMTP adicional'
                },
                {
                    'field': 'allow_self_improvement',
                    'prompt': '¿Permitir auto-mejora (crear herramientas/agentes)?',
                    'type': 'confirm',
                    'default': True,
                    'help': 'El agente podrá crear nuevas herramientas automáticamente'
                }
            ]
        },
        {
            'id': 'tools',
            'title': '🛠️ Herramientas Externas',
            'icon': '🛠️',
            'description': 'Configura integraciones con herramientas externas',
            'questions': [
                {
                    'field': 'browser_profile',
                    'prompt': 'Perfil de navegación web',
                    'type': 'select',
                    'options': [
                        {'name': '🔒 Headless - Sin interfaz (más seguro)', 'value': 'headless'},
                        {'name': '💾 Persistente - Guarda sesiones y cookies', 'value': 'persistent'},
                        {'name': '🚫 Deshabilitado - Sin navegación web', 'value': 'disabled'}
                    ],
                    'default': 'headless'
                },
                {
                    'field': 'git_name',
                    'prompt': 'Nombre para commits Git (opcional)',
                    'type': 'text',
                    'default': '',
                    'optional': True,
                    'help': 'Dejar vacío para no configurar Git'
                },
                {
                    'field': 'git_email',
                    'prompt': 'Email para commits Git (opcional)',
                    'type': 'text',
                    'default': '',
                    'optional': True,
                    'help': 'Dejar vacío para no configurar Git'
                },
                {
                    'field': 'ide_integration',
                    'prompt': '¿Integrar con VS Code / JetBrains?',
                    'type': 'confirm',
                    'default': False,
                    'help': 'Permite al agente interactuar con tu IDE'
                }
            ]
        },
        {
            'id': 'learning',
            'title': '📚 Capacidades de Aprendizaje',
            'icon': '📚',
            'description': 'Define cómo y qué puede aprender el agente',
            'questions': [
                {
                    'field': 'allow_language_learning',
                    'prompt': '¿Puede aprender nuevos lenguajes de programación?',
                    'type': 'confirm',
                    'default': True,
                    'help': 'El agente podrá aprender lenguajes no configurados inicialmente'
                },
                {
                    'field': 'preferred_languages',
                    'prompt': 'Lenguajes que ya conoce',
                    'type': 'checkbox',
                    'options': [
                        {'name': '🐍 Python', 'value': 'python'},
                        {'name': '📜 JavaScript', 'value': 'javascript'},
                        {'name': '📘 TypeScript', 'value': 'typescript'},
                        {'name': '🦀 Rust', 'value': 'rust'},
                        {'name': '☕ Java', 'value': 'java'},
                        {'name': '🐘 PHP', 'value': 'php'},
                        {'name': '🔹 Go', 'value': 'go'},
                        {'name': '🔷 C#', 'value': 'csharp'},
                        {'name': '🐛 C++', 'value': 'cpp'},
                        {'name': '🦎 Ruby', 'value': 'ruby'}
                    ],
                    'default': ['python'],
                    'help': 'Selecciona los lenguajes con los que el agente ya está familiarizado'
                },
                {
                    'field': 'learning_mode',
                    'prompt': 'Modo de aprendizaje',
                    'type': 'select',
                    'options': [
                        {'name': '🐢 Conservador - Solo fuentes oficiales', 'value': 'conservative'},
                        {'name': '⚖️ Balanceado - Mix de fuentes verificadas', 'value': 'balanced'},
                        {'name': '🚀 Agresivo - Todas las fuentes disponibles', 'value': 'aggressive'}
                    ],
                    'default': 'balanced'
                },
                {
                    'field': 'documentation_sources',
                    'prompt': 'Fuentes de documentación permitidas',
                    'type': 'checkbox',
                    'options': [
                        {'name': '📖 Documentación oficial', 'value': 'official_docs'},
                        {'name': '💬 Stack Overflow', 'value': 'stackoverflow'},
                        {'name': '🐙 GitHub', 'value': 'github'},
                        {'name': '📺 YouTube', 'value': 'youtube'},
                        {'name': '🎓 Cursos online', 'value': 'courses'},
                        {'name': '📝 Blogs técnicos', 'value': 'blogs'}
                    ],
                    'default': ['official_docs', 'github'],
                    'help': 'Fuentes que el agente puede consultar para aprender'
                }
            ]
        },
        {
            'id': 'hierarchy',
            'title': '🏢 Estructura de Equipo',
            'icon': '🏢',
            'description': 'Configura los agentes especializados del equipo',
            'questions': [
                {
                    'field': 'enable_all_agents',
                    'prompt': '¿Habilitar todos los agentes especializados?',
                    'type': 'confirm',
                    'default': True,
                    'help': 'Incluye Director, Arquitecto, Backend, Frontend, QA, etc.'
                },
                {
                    'field': 'priority_agents',
                    'prompt': 'Agentes prioritarios para tu stack',
                    'type': 'checkbox',
                    'options': [
                        {'name': '🔙 Backend Specialist', 'value': 'backend'},
                        {'name': '🎨 Frontend Specialist', 'value': 'frontend'},
                        {'name': '🗄️ Database Specialist', 'value': 'database'},
                        {'name': '🚀 DevOps Specialist', 'value': 'devops'},
                        {'name': '🔒 Security Specialist', 'value': 'security'},
                        {'name': '🧪 QA Specialist', 'value': 'qa'}
                    ],
                    'default': ['backend', 'database'],
                    'optional': True,
                    'help': 'Agentes que se activarán primero según tu stack'
                },
                {
                    'field': 'audit_frequency',
                    'prompt': 'Frecuencia de auditoría de código',
                    'type': 'select',
                    'options': [
                        {'name': 'Cada commit', 'value': 'every_commit'},
                        {'name': 'Diaria', 'value': 'daily'},
                        {'name': 'Semanal', 'value': 'weekly'},
                        {'name': 'Manual (solo cuando lo pidas)', 'value': 'manual'}
                    ],
                    'default': 'weekly'
                }
            ]
        },
        {
            'id': 'system',
            'title': '⚙️ Configuración del Sistema',
            'icon': '⚙️',
            'description': 'Ajustes técnicos del sistema',
            'questions': [
                {
                    'field': 'sandbox_enabled',
                    'prompt': '¿Habilitar sandbox Docker para ejecución de código?',
                    'type': 'confirm',
                    'default': True,
                    'help': 'Recomendado para seguridad. Requiere Docker instalado.'
                },
                {
                    'field': 'max_concurrent_agents',
                    'prompt': 'Máximo agentes ejecutándose simultáneamente',
                    'type': 'number',
                    'default': 3,
                    'min': 1,
                    'max': 10,
                    'help': 'Afecta el rendimiento. Más agentes = más uso de RAM'
                },
                {
                    'field': 'log_level',
                    'prompt': 'Nivel de logging',
                    'type': 'select',
                    'options': [
                        {'name': '🔴 ERROR - Solo errores', 'value': 'ERROR'},
                        {'name': '🟠 WARNING - Advertencias y errores', 'value': 'WARNING'},
                        {'name': '🟡 INFO - Información general', 'value': 'INFO'},
                        {'name': '🟢 DEBUG - Todo el detalle', 'value': 'DEBUG'}
                    ],
                    'default': 'INFO'
                }
            ]
        }
    ]

    def __init__(self, resume: bool = False):
        """
        Inicializa el wizard.

        Args:
            resume: Si True, intenta recuperar progreso guardado temporalmente
        """
        self.answers: Dict[str, Any] = {}
        self.current_step = 0
        self.completed_steps: list = []

        # ✅ Cargar progreso temporal si existe y se solicita
        if resume and self.TEMP_FILE.exists():
            self._load_temp_progress()
            print(f"📥 Progreso recuperado: {len(self.completed_steps)} pasos completados")

    # ===========================================
    # ✅ NUEVO: Sistema de Guardado Temporal
    # ===========================================

    def _save_temp_progress(self) -> None:
        """Guarda progreso actual en archivo temporal"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        temp_data = {
            'answers': self.answers,
            'completed_steps': self.completed_steps,
            'current_step': self.current_step,
            'timestamp': datetime.now().isoformat()
        }

        with open(self.TEMP_FILE, 'w', encoding='utf-8') as f:
            json.dump(temp_data, f, indent=2, default=str)

    def _load_temp_progress(self) -> bool:
        """Carga progreso desde archivo temporal"""
        try:
            if not self.TEMP_FILE.exists():
                return False

            with open(self.TEMP_FILE, 'r', encoding='utf-8') as f:
                temp_data = json.load(f)

            self.answers = temp_data.get('answers', {})
            self.completed_steps = temp_data.get('completed_steps', [])
            self.current_step = temp_data.get('current_step', 0)

            return True
        except Exception as e:
            print(f"⚠️ No se pudo recuperar progreso: {e}")
            return False

    def _clear_temp_progress(self) -> None:
        """Elimina archivo temporal después de guardar permanentemente"""
        if self.TEMP_FILE.exists():
            self.TEMP_FILE.unlink()

    # ===========================================
    # MÉTODOS PRINCIPALES DEL WIZARD
    # ===========================================

    def run(self, resume: bool = False) -> AgentConfig:
        """
        Ejecuta el wizard completo.

        Args:
            resume: Intentar recuperar progreso previo

        Returns:
            AgentConfig: Configuración creada
        """
        self._print_header()

        # Si hay progreso recuperado, preguntar si continuar
        if resume and self.completed_steps:
            if not questionary.confirm(
                    f"¿Continuar desde el paso {len(self.completed_steps) + 1}?",
                    default=True
            ).ask():
                self.answers = {}
                self.completed_steps = []
                self.current_step = 0
                print("🔄 Reiniciando wizard desde el inicio...\n")

        for i, step in enumerate(self.STEPS):
            # Saltar pasos ya completados si hay recuperación
            if step['id'] in self.completed_steps:
                print(f"⏭️  Saltando paso ya completado: {step['title']}")
                continue

            self.current_step = i
            self._run_step(step)
            self.completed_steps.append(step['id'])

            # ✅ Guardar progreso temporal después de cada paso
            self._save_temp_progress()

        # Construir configuración final
        config = self._build_config()

        # Guardar configuración permanentemente
        self._save_config(config)

        # ✅ Limpiar archivo temporal
        self._clear_temp_progress()

        # Mostrar resumen
        self._print_summary(config)

        return config

    def _print_header(self) -> None:
        """Imprime el encabezado del wizard"""
        print("\n" + "=" * 70)
        print("  🧙‍♂️  DEV MIND - Wizard de Configuración Inicial")
        print("=" * 70)
        print("\nEste wizard te guiará para configurar tu agente de desarrollo.")
        print("Puedes cambiar cualquier configuración después con 'devmind config'.")
        print("\n💡 Tip: Si se interrumpe, ejecuta 'devmind init' nuevamente para continuar.")
        print("\n" + "-" * 70 + "\n")

    def _run_step(self, step: Dict[str, Any]) -> None:
        """
        Ejecuta un paso del wizard.

        Args:
            step: Definición del paso
        """
        print(f"\n{step['icon']} {step['title']}")
        print(f"   {step['description']}")
        print(f"   Paso {self.current_step + 1} de {len(self.STEPS)}")
        print("-" * 70)

        for question in step['questions']:
            answer = self._ask_question(question)
            if answer is not None:
                self._store_answer(question['field'], answer, step['id'])

        print(f"✅ {step['title']} completado\n")

    def _ask_question(self, question: Dict[str, Any]) -> Any:
        """
        Hace una pregunta y retorna la respuesta.

        Args:
            question: Definición de la pregunta

        Returns:
            Any: Respuesta del usuario
        """
        q_type = question['type']
        prompt = question['prompt']

        # Mostrar ayuda si existe
        if 'help' in question:
            print(f"   💡 {question['help']}")

        if q_type == 'text':
            return questionary.text(
                prompt,
                default=question.get('default', ''),
                validate=lambda x: question.get('validate', lambda y: True)(x) if question.get('validate') else True
            ).ask()

        elif q_type == 'select':
            choices = [opt['name'] for opt in question['options']]
            default = question.get('default')

            if default:
                default_idx = next(
                    (i for i, opt in enumerate(question['options']) if opt['value'] == default),
                    0
                )
            else:
                default_idx = 0

            selected = questionary.select(
                prompt,
                choices=choices,
                default=choices[default_idx] if choices and 0 <= default_idx < len(choices) else None
            ).ask()

            # Mapear nombre a valor
            if selected:
                return next(
                    (opt['value'] for opt in question['options'] if opt['name'] == selected),
                    selected
                )
            return None

        elif q_type == 'confirm':
            return questionary.confirm(
                prompt,
                default=question.get('default', False)
            ).ask()

        elif q_type == 'number':
            def validate_number(x):
                try:
                    val = int(x)
                    min_val = question.get('min', 0)
                    max_val = question.get('max', float('inf'))
                    return min_val <= val <= max_val
                except ValueError:
                    return False

            result = questionary.text(
                prompt,
                default=str(question.get('default', 0)),
                validate=lambda x: validate_number(x)
            ).ask()

            return int(result) if result and result.isdigit() else question.get('default', 0)

        elif q_type == 'checkbox':
            # === FIX PARA CHECKBOX: Sin default para evitar errores ===
            choice_names = [opt['name'] for opt in question['options']]
            default_values = question.get('default', [])

            # Mostrar mensaje de valores sugeridos
            if default_values:
                default_display = [
                    opt['name'] for opt in question['options']
                    if opt['value'] in default_values
                ]
                if default_display:
                    print(f"   📌 Sugerencia: {', '.join(default_display)}")

            selected_names = questionary.checkbox(
                prompt,
                choices=choice_names
                # Sin default para evitar errores de matching con questionary
            ).ask()

            # Mapear nombres seleccionados a valores
            if selected_names:
                return [
                    next((opt['value'] for opt in question['options'] if opt['name'] == name), name)
                    for name in selected_names
                ]
            # Si no seleccionó nada pero hay defaults, usar defaults
            elif default_values:
                return default_values
            return []

        return None

    def _store_answer(self, field: str, answer: Any, step_id: str) -> None:
        """
        Almacena la respuesta.

        Args:
            field: Nombre del campo
            answer: Respuesta del usuario
            step_id: ID del paso
        """
        if field.startswith('git_'):
            # Inicializar dict si no existe
            if 'git_config' not in self.answers:
                self.answers['git_config'] = {}

            key = field.replace('git_', '')
            # ✅ Siempre guardar el valor (incluso cadena vacía)
            # Esto permite edición manual posterior del JSON
            self.answers['git_config'][key] = str(answer).strip() if answer else ""
        else:
            self.answers[field] = answer

    def _build_config(self) -> AgentConfig:
        """
        Construye el objeto de configuración.

        Returns:
            AgentConfig: Configuración completa
        """
        # Mapear respuestas a enums
        if 'personality' in self.answers:
            self.answers['personality'] = PersonalityType(self.answers['personality'])
        if 'autonomy_mode' in self.answers:
            self.answers['autonomy_mode'] = AutonomyMode(self.answers['autonomy_mode'])
        if 'learning_mode' in self.answers:
            self.answers['learning_mode'] = LearningMode(self.answers['learning_mode'])
        if 'audit_frequency' in self.answers:
            self.answers['audit_frequency'] = AuditFrequency(self.answers['audit_frequency'])

        # ✅ FIX: Construir GitConfig SOLO si hay nombre Y email
        git_data = self.answers.get('git_config', {})
        if isinstance(git_data, dict):
            # Crear GitConfig con valores (pueden ser vacíos)
            self.answers['git_config'] = GitConfig(
                name=git_data.get('name', ""),
                email=git_data.get('email', "")
            )
        elif isinstance(git_data, GitConfig):
            # Ya es una instancia, dejarla como está
            pass
        else:
            # Fallback: crear instancia vacía
            self.answers['git_config'] = GitConfig()

        # Marcar como inicializado
        self.answers['initialized'] = True

        return AgentConfig(**self.answers)

    def _save_config(self, config: AgentConfig) -> None:
        """
        Guarda la configuración en archivo permanente.

        Args:
            config: Configuración a guardar
        """
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        # Excluir campos que no queremos persistir
        config_dict = config.model_dump(
            exclude={'created_at', 'updated_at'},
            by_alias=True,
            mode='json'
        )

        with open(self.CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, default=str)

        # Crear directorios adicionales
        (self.CONFIG_DIR / "projects").mkdir(exist_ok=True)
        (self.CONFIG_DIR / "profiles").mkdir(exist_ok=True)

    def _print_summary(self, config: AgentConfig) -> None:
        """
        Imprime resumen de configuración.

        Args:
            config: Configuración creada
        """
        print("\n" + "=" * 70)
        print("  ✅ ¡Configuración completada exitosamente!")
        print("=" * 70)
        print(f"\n📁 Configuración guardada en: {self.CONFIG_FILE}")
        print(f"\n🤖 Resumen de tu agente:")
        print(f"   • Nombre: {config.agent_name}")
        print(f"   • Personalidad: {config.personality}")
        print(f"   • Modo de autonomía: {config.autonomy_mode}")
        print(f"   • Lenguajes: {', '.join(config.preferred_languages)}")
        print(f"   • Sandbox: {'✅ Habilitado' if config.sandbox_enabled else '❌ Deshabilitado'}")

        # Mostrar Git config si existe
        if config.git_config:
            print(f"   • Git: {config.git_config.name} <{config.git_config.email}>")

        print(f"\n🚀 Para comenzar:")
        print(f"   • devmind chat          - Iniciar conversación")
        print(f"   • devmind status        - Ver estado del sistema")
        print(f"   • devmind config        - Modificar configuración")
        print("\n" + "=" * 70 + "\n")