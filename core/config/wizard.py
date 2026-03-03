import questionary
from pathlib import Path
from typing import Dict, Any
import json

from .schema import AgentConfig, PersonalityType, AutonomyMode, LearningMode, AuditFrequency


class OnboardingWizard:
    """Wizard interactivo para configuración inicial"""

    CONFIG_DIR = Path.home() / ".devmind"
    CONFIG_FILE = CONFIG_DIR / "config.json"

    STEPS = [
        {
            'id': 'identity',
            'title': '🆔 Identidad del Agente',
            'icon': '🆔',
            'questions': [
                {
                    'field': 'agent_name',
                    'prompt': '¿Cómo quieres llamar a tu agente?',
                    'type': 'text',
                    'default': 'DevMind',
                    'validate': lambda x: len(x) >= 1 and len(x) <= 50
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
                    ]
                },
                {
                    'field': 'communication_style',
                    'prompt': 'Estilo de comunicación',
                    'type': 'select',
                    'options': [
                        {'name': '⚡ Conciso - Respuestas breves', 'value': 'concise'},
                        {'name': '📖 Detallado - Explicaciones completas', 'value': 'detailed'},
                        {'name': '🎓 Educativo - Enseña mientras trabaja', 'value': 'educational'}
                    ]
                }
            ]
        },
        {
            'id': 'capabilities',
            'title': '⚡ Capacidades y Permisos',
            'icon': '⚡',
            'questions': [
                {
                    'field': 'autonomy_mode',
                    'prompt': 'Nivel de autonomía',
                    'type': 'select',
                    'options': [
                        {'name': '🛡️ Supervisado - Pide confirmación para todo', 'value': 'supervised'},
                        {'name': '⚖️ Semi-Autónomo - Autonomía para tareas simples', 'value': 'semi_autonomous'},
                        {'name': '🚀 Full Autónomo - Ejecuta sin preguntar (sandbox)', 'value': 'full_autonomous'}
                    ]
                },
                {
                    'field': 'max_file_write_without_confirm',
                    'prompt': 'Máximo archivos a escribir sin confirmar',
                    'type': 'number',
                    'default': 5,
                    'min': 1,
                    'max': 50
                },
                {
                    'field': 'allow_internet',
                    'prompt': '¿Permitir acceso a internet?',
                    'type': 'confirm',
                    'default': False
                },
                {
                    'field': 'allow_email',
                    'prompt': '¿Permitir envío/lectura de emails?',
                    'type': 'confirm',
                    'default': False
                },
                {
                    'field': 'allow_self_improvement',
                    'prompt': '¿Permitir auto-mejora (crear herramientas/agentes)?',
                    'type': 'confirm',
                    'default': True
                }
            ]
        },
        {
            'id': 'tools',
            'title': '🛠️ Herramientas Externas',
            'icon': '🛠️',
            'questions': [
                {
                    'field': 'browser_profile',
                    'prompt': 'Perfil de navegación web',
                    'type': 'select',
                    'options': [
                        {'name': '🔒 Headless - Sin interfaz (más seguro)', 'value': 'headless'},
                        {'name': '💾 Persistente - Guarda sesiones', 'value': 'persistent'},
                        {'name': '🚫 Deshabilitado - Sin navegación', 'value': 'disabled'}
                    ]
                },
                {
                    'field': 'git_name',
                    'prompt': 'Nombre para commits Git',
                    'type': 'text',
                    'default': '',
                    'optional': True
                },
                {
                    'field': 'git_email',
                    'prompt': 'Email para commits Git',
                    'type': 'text',
                    'default': '',
                    'optional': True
                }
            ]
        },
        {
            'id': 'learning',
            'title': '📚 Capacidades de Aprendizaje',
            'icon': '📚',
            'questions': [
                {
                    'field': 'allow_language_learning',
                    'prompt': '¿Puede aprender nuevos lenguajes de programación?',
                    'type': 'confirm',
                    'default': True
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
                        {'name': '🔷 C#', 'value': 'csharp'}
                    ],
                    'default': ['python']
                },
                {
                    'field': 'learning_mode',
                    'prompt': 'Modo de aprendizaje',
                    'type': 'select',
                    'options': [
                        {'name': '🐢 Conservador - Solo fuentes oficiales', 'value': 'conservative'},
                        {'name': '⚖️ Balanceado - Mix de fuentes', 'value': 'balanced'},
                        {'name': '🚀 Agresivo - Todas las fuentes disponibles', 'value': 'aggressive'}
                    ]
                }
            ]
        },
        {
            'id': 'hierarchy',
            'title': '🏢 Estructura de Equipo',
            'icon': '🏢',
            'questions': [
                {
                    'field': 'enable_all_agents',
                    'prompt': '¿Habilitar todos los agentes especializados?',
                    'type': 'confirm',
                    'default': True
                },
                {
                    'field': 'audit_frequency',
                    'prompt': 'Frecuencia de auditoría de código',
                    'type': 'select',
                    'options': [
                        {'name': 'Cada commit', 'value': 'every_commit'},
                        {'name': 'Diaria', 'value': 'daily'},
                        {'name': 'Semanal', 'value': 'weekly'},
                        {'name': 'Manual', 'value': 'manual'}
                    ]
                }
            ]
        }
    ]

    def __init__(self):
        self.answers = {}

    def run(self) -> AgentConfig:
        """Ejecuta el wizard completo"""
        print("\n" + "=" * 60)
        print("🧙‍♂️  DEV MIND - Wizard de Configuración Inicial")
        print("=" * 60 + "\n")

        for step in self.STEPS:
            self._run_step(step)

        # Crear configuración final
        config = self._build_config()

        # Guardar configuración
        self._save_config(config)

        # Inicializar agentes
        self._initialize_agents(config)

        print("\n" + "=" * 60)
        print("✅ ¡Configuración completada exitosamente!")
        print("=" * 60)
        print(f"\n📁 Configuración guardada en: {self.CONFIG_FILE}")
        print(f"🤖 Nombre del agente: {config.agent_name}")
        print(f"⚡ Modo de autonomía: {config.autonomy_mode}")
        print(f"\n🚀 Para comenzar: devmind chat\n")

        return config

    def _run_step(self, step: Dict[str, Any]):
        """Ejecuta un paso del wizard"""
        print(f"\n{step['icon']} {step['title']}")
        print("-" * 40)

        for question in step['questions']:
            answer = self._ask_question(question)
            self._store_answer(question['field'], answer, step['id'])

    def _ask_question(self, question: Dict[str, Any]) -> Any:
        """Hace una pregunta y retorna la respuesta"""
        q_type = question['type']

        if q_type == 'text':
            return questionary.text(
                question['prompt'],
                default=question.get('default', ''),
                validate=lambda x: question.get('validate', lambda y: True)(x)
            ).ask()

        elif q_type == 'select':
            return questionary.select(
                question['prompt'],
                choices=[opt['name'] for opt in question['options']],
                default=next((opt['name'] for opt in question['options']
                              if opt['value'] == question.get('default')), None)
            ).ask()

        elif q_type == 'confirm':
            return questionary.confirm(
                question['prompt'],
                default=question.get('default', False)
            ).ask()

        elif q_type == 'number':
            return int(questionary.text(
                question['prompt'],
                default=str(question.get('default', 0)),
                validate=lambda x: x.isdigit()
            ).ask())

        elif q_type == 'checkbox':
            return questionary.checkbox(
                question['prompt'],
                choices=[opt['name'] for opt in question['options']],
                default=[opt['name'] for opt in question['options']
                         if opt['value'] in question.get('default', [])]
            ).ask()

        return None

    def _store_answer(self, field: str, answer: Any, step_id: str):
        """Almacena la respuesta"""
        # Manejar campos compuestos (git_name, git_email -> git_config)
        if field.startswith('git_'):
            if 'git_config' not in self.answers:
                self.answers['git_config'] = {}
            key = field.replace('git_', '')
            if answer:
                self.answers['git_config'][key] = answer
        else:
            self.answers[field] = answer

    def _build_config(self) -> AgentConfig:
        """Construye el objeto de configuración"""
        # Mapear respuestas a enums
        if 'personality' in self.answers:
            self.answers['personality'] = PersonalityType(self.answers['personality'])
        if 'autonomy_mode' in self.answers:
            self.answers['autonomy_mode'] = AutonomyMode(self.answers['autonomy_mode'])
        if 'learning_mode' in self.answers:
            self.answers['learning_mode'] = LearningMode(self.answers['learning_mode'])
        if 'audit_frequency' in self.answers:
            self.answers['audit_frequency'] = AuditFrequency(self.answers['audit_frequency'])

        # Mapear nombres de checkbox a valores
        if 'preferred_languages' in self.answers:
            lang_map = {
                '🐍 Python': 'python',
                '📜 JavaScript': 'javascript',
                '📘 TypeScript': 'typescript',
                '🦀 Rust': 'rust',
                '☕ Java': 'java',
                '🐘 PHP': 'php',
                '🔹 Go': 'go',
                '🔷 C#': 'csharp'
            }
            self.answers['preferred_languages'] = [
                lang_map.get(name, name) for name in self.answers['preferred_languages']
            ]

        self.answers['initialized'] = True
        return AgentConfig(**self.answers)

    def _save_config(self, config: AgentConfig):
        """Guarda la configuración en archivo"""
        self.CONFIG_DIR.mkdir(parents=True, exist_ok=True)

        with open(self.CONFIG_FILE, 'w') as f:
            json.dump(config.dict(), f, indent=2, default=str)

    def _initialize_agents(self, config: AgentConfig):
        """Inicializa los agentes según configuración"""
        # Esto se implementará en la Fase 1
        print("\n🤖 Inicializando agentes...")
        # from core.agents.registry import AgentRegistry
        # AgentRegistry.initialize(config)