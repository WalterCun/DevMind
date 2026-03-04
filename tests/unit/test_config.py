# devmind-core/tests/unit/test_config.py
"""
Tests unitarios para el módulo de configuración.
"""

import pytest

from core.config.manager import ConfigManager
from core.config.schema import (
    AgentConfig,
    PersonalityType,
    AutonomyMode,
    EmailConfig,
    GitConfig,
)


class TestAgentConfig:
    """Tests para el esquema AgentConfig"""

    def test_default_values(self):
        """Verifica valores por defecto"""
        config = AgentConfig()

        assert config.agent_name == "DevMind"
        assert config.personality == PersonalityType.PROFESSIONAL
        assert config.autonomy_mode == AutonomyMode.SUPERVISED
        assert config.sandbox_enabled is True
        assert config.initialized is False

    def test_custom_values(self):
        """Verifica valores personalizados"""
        config = AgentConfig(
            agent_name="TestBot",
            personality=PersonalityType.CASUAL,
            autonomy_mode=AutonomyMode.FULL_AUTONOMOUS,
            preferred_languages=["python", "javascript"]
        )

        assert config.agent_name == "TestBot"
        assert config.personality == PersonalityType.CASUAL
        assert len(config.preferred_languages) == 2

    def test_invalid_language(self):
        """Verifica validación de lenguajes inválidos"""
        with pytest.raises(ValueError):
            AgentConfig(preferred_languages=["invalid_language"])

    def test_system_prompt_generation(self):
        """Verifica generación de prompt del sistema"""
        config = AgentConfig(agent_name="TestAgent")
        prompt = config.get_system_prompt()

        assert "TestAgent" in prompt
        assert "profesional" in prompt.lower() or "Professional" in prompt

    def test_can_execute_autonomously(self):
        """Verifica lógica de ejecución autónoma"""
        supervised = AgentConfig(autonomy_mode=AutonomyMode.SUPERVISED)
        full_auto = AgentConfig(autonomy_mode=AutonomyMode.FULL_AUTONOMOUS)

        assert supervised.can_execute_autonomously("read_file") is False
        assert full_auto.can_execute_autonomously("read_file") is True


class TestConfigManager:
    """Tests para ConfigManager"""

    def test_singleton_pattern(self):
        """Verifica patrón Singleton"""
        manager1 = ConfigManager()
        manager2 = ConfigManager()

        assert manager1 is manager2

    def test_is_initialized(self):
        """Verifica detección de inicialización"""
        manager = ConfigManager()

        # Depende del estado del sistema
        # Este test verifica que el método existe y retorna bool
        result = manager.is_initialized()
        assert isinstance(result, bool)

    def test_get_security_settings(self):
        """Verifica obtención de configuración de seguridad"""
        manager = ConfigManager()

        if manager.is_initialized():
            settings = manager.get_security_settings()
            assert 'autonomy_mode' in settings
            assert 'sandbox_enabled' in settings


class TestEmailConfig:
    """Tests para EmailConfig"""

    def test_valid_email_config(self):
        """Verifica configuración de email válida"""
        config = EmailConfig(
            smtp_server="smtp.example.com",
            smtp_port=587,
            username="user@example.com",
            password="secret"
        )

        assert config.smtp_server == "smtp.example.com"
        assert config.use_tls is True

    def test_invalid_smtp_server(self):
        """Verifica validación de servidor SMTP"""
        with pytest.raises(ValueError):
            EmailConfig(
                smtp_server="invalid",
                username="user",
                password="pass"
            )


class TestGitConfig:
    """Tests para GitConfig"""

    def test_valid_git_config(self):
        """Verifica configuración de Git válida"""
        config = GitConfig(
            name="Test User",
            email="test@example.com"
        )

        assert config.name == "Test User"
        assert config.email == "test@example.com"

    def test_invalid_email(self):
        """Verifica validación de email"""
        with pytest.raises(ValueError):
            GitConfig(
                name="Test User",
                email="invalid-email"
            )