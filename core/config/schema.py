from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PersonalityType(str, Enum):
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    TECHNICAL = "technical"
    MENTOR = "mentor"


class AutonomyMode(str, Enum):
    SUPERVISED = "supervised"
    SEMI_AUTONOMOUS = "semi_autonomous"
    FULL_AUTONOMOUS = "full_autonomous"


class LearningMode(str, Enum):
    CONSERVATIVE = "conservative"
    BALANCED = "balanced"
    AGGRESSIVE = "aggressive"


class AuditFrequency(str, Enum):
    EVERY_COMMIT = "every_commit"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"


class EmailConfig(BaseModel):
    smtp_server: str
    smtp_port: int = 587
    username: str
    password: str
    use_tls: bool = True


class GitConfig(BaseModel):
    name: str
    email: str


class AgentConfig(BaseModel):
    """Configuración principal del agente"""
    # Identidad
    agent_name: str = Field(default="DevMind", min_length=1, max_length=50)
    personality: PersonalityType = Field(default=PersonalityType.PROFESSIONAL)
    communication_style: str = Field(default="concise")

    # Capacidades
    autonomy_mode: AutonomyMode = Field(default=AutonomyMode.SUPERVISED)
    max_file_write_without_confirm: int = Field(default=5, ge=1, le=50)
    allow_internet: bool = False
    allow_email: bool = False
    allow_self_improvement: bool = True

    # Herramientas
    email_config: Optional[EmailConfig] = None
    browser_profile: str = Field(default="headless")
    git_config: Optional[GitConfig] = None
    ide_integration: bool = False

    # Aprendizaje
    allow_language_learning: bool = True
    preferred_languages: List[str] = Field(default=["python"])
    learning_mode: LearningMode = Field(default=LearningMode.BALANCED)
    documentation_sources: List[str] = Field(default=["official_docs"])

    # Jerarquía de Agentes
    enable_all_agents: bool = True
    priority_agents: List[str] = Field(default=[])
    audit_frequency: AuditFrequency = Field(default=AuditFrequency.WEEKLY)

    # Sistema
    sandbox_enabled: bool = True
    max_concurrent_agents: int = Field(default=3, ge=1, le=10)
    log_level: str = Field(default="INFO")

    # Metadata
    initialized: bool = False
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    version: str = Field(default="0.1.0")

    @validator('preferred_languages')
    def validate_languages(cls, v):
        valid_langs = ['python', 'javascript', 'typescript', 'go', 'rust',
                       'java', 'php', 'ruby', 'csharp', 'cpp']
        for lang in v:
            if lang.lower() not in valid_langs:
                raise ValueError(f'Lenguaje no soportado: {lang}')
        return v

    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }