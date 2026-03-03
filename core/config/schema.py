# devmind-core/core/config/schema.py
"""
Esquemas de configuración usando Pydantic v2.

Define la estructura de datos para la configuración del agente,
incluyendo identidad, capacidades, herramientas y preferencias.
"""

import re
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, field_validator, model_validator


class PersonalityType(str, Enum):
    """Tipos de personalidad del agente"""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    MENTOR = "mentor"


class AutonomyMode(str, Enum):
    """Niveles de autonomía del agente"""
    SUPERVISED = "supervised"
    SEMI_AUTONOMOUS = "semi_autonomous"
    FULL_AUTONOMOUS = "full_autonomous"


class LearningMode(str, Enum):
    """Modos de aprendizaje del agente"""
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class AuditFrequency(str, Enum):
    """Frecuencia de auditoría de código"""
    EVERY_COMMIT = "every_commit"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class EmailConfig(BaseModel):
    """Configuración para envío/lectura de emails"""
    smtp_server: str = Field(..., min_length=1)
    smtp_port: int = Field(default=587, ge=1, le=65535)
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)
    use_tls: bool = Field(default=True)

    @field_validator('smtp_server')
    @classmethod
    def validate_smtp_server(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('SMTP server debe ser un dominio válido')
        return v


class GitConfig(BaseModel):
    """Configuración para commits de Git"""
    name: str = Field(
        default="",  # ✅ Default vacío en lugar de requerido
        description="Nombre para commits Git"
    )
    email: str = Field(
        default="",  # ✅ Default vacío en lugar de requerido
        description="Email para commits Git"
    )

    @field_validator('email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Solo validar si el email no está vacío"""
        if v and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', v):
            raise ValueError('Email inválido')
        return v

    @property
    def is_configured(self) -> bool:
        """Verifica si Git está completamente configurado"""
        return bool(self.name and self.email)


class AgentConfig(BaseModel):
    """
    Configuración principal del agente DevMind.

    Esta clase define todas las preferencias, capacidades y restricciones
    que gobiernan el comportamiento del agente autónomo.
    """

    # ===========================================
    # IDENTIDAD DEL AGENTE
    # ===========================================
    agent_name: str = Field(
        default="DevMind",
        min_length=1,
        max_length=50,
        description="Nombre del agente"
    )
    personality: PersonalityType = Field(
        default=PersonalityType.PROFESSIONAL,
        description="Personalidad del agente"
    )
    communication_style: str = Field(
        default="concise",
        description="Estilo de comunicación"
    )

    # ===========================================
    # CAPACIDADES Y PERMISOS
    # ===========================================
    autonomy_mode: AutonomyMode = Field(
        default=AutonomyMode.SUPERVISED,
        description="Nivel de autonomía"
    )
    max_file_write_without_confirm: int = Field(
        default=5,
        ge=1,
        le=50,
        description="Máximo archivos a escribir sin confirmar"
    )
    allow_internet: bool = Field(
        default=False,
        description="Permitir acceso a internet"
    )
    allow_email: bool = Field(
        default=False,
        description="Permitir envío/lectura de emails"
    )
    allow_self_improvement: bool = Field(
        default=True,
        description="Permitir auto-mejora (crear herramientas/agentes)"
    )

    # ===========================================
    # HERRAMIENTAS EXTERNAS
    # ===========================================
    email_config: Optional[EmailConfig] = Field(
        default=None,
        description="Configuración SMTP"
    )
    browser_profile: str = Field(
        default="headless",
        description="Perfil de navegación web"
    )
    git_config: GitConfig = Field(  # ✅ Siempre existe, con valores vacíos por defecto
        default_factory=GitConfig,
        description="Configuración Git (puede tener valores vacíos)"
    )
    ide_integration: bool = Field(
        default=False,
        description="Integrar con VS Code / JetBrains"
    )

    # ===========================================
    # APRENDIZAJE
    # ===========================================
    allow_language_learning: bool = Field(
        default=True,
        description="Puede aprender nuevos lenguajes"
    )
    preferred_languages: List[str] = Field(
        default=["python"],
        description="Lenguajes conocidos inicialmente"
    )
    learning_mode: LearningMode = Field(
        default=LearningMode.BALANCED,
        description="Modo de aprendizaje"
    )
    documentation_sources: List[str] = Field(
        default=["official_docs"],
        description="Fuentes de documentación permitidas"
    )

    # ===========================================
    # JERARQUÍA DE AGENTES
    # ===========================================
    enable_all_agents: bool = Field(
        default=True,
        description="Habilitar todos los agentes especializados"
    )
    priority_agents: List[str] = Field(
        default=[],
        description="Agentes prioritarios para tu stack"
    )
    audit_frequency: AuditFrequency = Field(
        default=AuditFrequency.WEEKLY,
        description="Frecuencia de auditoría"
    )

    # ===========================================
    # SISTEMA
    # ===========================================
    sandbox_enabled: bool = Field(
        default=True,
        description="Sandbox Docker habilitado"
    )
    max_concurrent_agents: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Máximo agentes concurrentes"
    )
    log_level: str = Field(
        default="INFO",
        description="Nivel de logging"
    )

    # ===========================================
    # METADATA
    # ===========================================
    initialized: bool = Field(
        default=False,
        description="Si el wizard fue completado"
    )
    created_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de creación"
    )
    updated_at: datetime = Field(
        default_factory=datetime.now,
        description="Fecha de última actualización"
    )
    version: str = Field(
        default="0.1.0",
        description="Versión del esquema de configuración"
    )

    # ===========================================
    # VALIDADORES DE CAMPO (Pydantic v2)
    # ===========================================
    @field_validator('preferred_languages')
    @classmethod
    def validate_languages(cls, v: List[str]) -> List[str]:
        """Valida que los lenguajes estén soportados"""
        valid_langs = [
            'python', 'javascript', 'typescript', 'go', 'rust',
            'java', 'php', 'ruby', 'csharp', 'cpp', 'swift', 'kotlin'
        ]
        for lang in v:
            if lang.lower() not in valid_langs:
                raise ValueError(f'Lenguaje no soportado: {lang}. Opciones: {valid_langs}')
        return [lang.lower() for lang in v]

    @field_validator('documentation_sources')
    @classmethod
    def validate_doc_sources(cls, v: List[str]) -> List[str]:
        """Valida fuentes de documentación"""
        valid_sources = [
            'official_docs', 'stackoverflow', 'github', 'youtube',
            'courses', 'blogs', 'books'
        ]
        for source in v:
            if source not in valid_sources:
                raise ValueError(f'Fuente no válida: {source}')
        return v

    @field_validator('browser_profile')
    @classmethod
    def validate_browser_profile(cls, v: str) -> str:
        """Valida perfil de navegador"""
        valid_profiles = ['headless', 'persistent', 'disabled']
        if v not in valid_profiles:
            raise ValueError(f'Perfil inválido: {v}')
        return v

    # ===========================================
    # VALIDADOR DE MODELO
    # ===========================================
    @model_validator(mode='after')
    def validate_email_config(self) -> 'AgentConfig':
        """Valida que email_config exista si allow_email es True"""
        if self.allow_email and not self.email_config:
            raise ValueError('email_config es requerido si allow_email es True')
        return self

    # ===========================================
    # MÉTODOS AUXILIARES
    # ===========================================
    def get_system_prompt(self) -> str:
        """Genera el prompt del sistema basado en la configuración"""
        personality_prompts = {
            PersonalityType.PROFESSIONAL: "Eres profesional, formal y directo en tus respuestas.",
            PersonalityType.CASUAL: "Eres amigable, relajado y cercano en tus respuestas.",
            PersonalityType.TECHNICAL: "Eres detallado, preciso y técnico en tus respuestas.",
            PersonalityType.MENTOR: "Eres educativo, paciente y explicativo en tus respuestas."
        }

        return f"""Eres {self.agent_name}, un ingeniero de software autónomo.

{personality_prompts.get(self.personality, '')}

Estilo de comunicación: {self.communication_style}
Modo de autonomía: {self.autonomy_mode.value}
Lenguajes conocidos: {', '.join(self.preferred_languages)}

Reglas importantes:
- Nunca ejecutes código sin permiso en modo supervisado
- Siempre valida tus cambios antes de aplicarlos
- Documenta tus decisiones arquitectónicas
- Reporta bugs y problemas de seguridad inmediatamente
"""

    def can_execute_autonomously(self, action_type: str) -> bool:
        """Verifica si puede ejecutar una acción autónomamente"""
        if self.autonomy_mode == AutonomyMode.FULL_AUTONOMOUS:
            return True
        elif self.autonomy_mode == AutonomyMode.SEMI_AUTONOMOUS:
            return action_type in ['read_file', 'write_code', 'run_tests']
        return False

    def get_git_signature(self) -> Optional[str]:
        """
        Obtiene la firma Git para commits.

        Returns:
            str en formato "Name <email>" o None si no está configurado
        """
        if self.git_config and self.git_config.is_configured:
            return f"{self.git_config.name} <{self.git_config.email}>"
        return None

    # ===========================================
    # SERIALIZACIÓN COMPATIBLE (Pydantic v2)
    # ===========================================
    def model_dump_compat(self, **kwargs) -> Dict[str, Any]:
        """Wrapper compatible para dict() de Pydantic v1"""
        return self.model_dump(**kwargs)

    def model_dump_json_compat(self, **kwargs) -> str:
        """Wrapper compatible para json() de Pydantic v1"""
        return self.model_dump_json(**kwargs)
