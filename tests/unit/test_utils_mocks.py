# devmind-core/tests/unit/test_utils_mocks.py
"""
Tests para verificar que las factories de mocks funcionan correctamente.
"""

import pytest
from core.agents.base import AgentLevel, AgentStatus


class TestMockAgentFactory:
    """Tests para el factory de mock agents"""

    def test_create_basic_mock(self, mock_agent_factory):
        """Verifica creación de mock básico"""
        agent = mock_agent_factory()

        assert agent.id == "mock_agent_001"
        assert agent.name == "Mock Agent"
        assert agent.role == "Test Role"
        assert agent.level == AgentLevel.EXECUTION
        assert agent.status == AgentStatus.IDLE

    def test_create_custom_mock(self, mock_agent_factory):
        """Verifica creación de mock con parámetros personalizados"""
        agent = mock_agent_factory(
            agent_id="custom_999",
            name="Custom Bot",
            role="Custom Role",
            level=AgentLevel.STRATEGIC,
            tasks_completed=42,
            tasks_failed=1
        )

        assert agent.id == "custom_999"
        assert agent.name == "Custom Bot"
        assert agent.role == "Custom Role"
        assert agent.level == AgentLevel.STRATEGIC
        assert agent.tasks_completed == 42
        assert agent.tasks_failed == 1

    def test_get_status_returns_dict(self, mock_agent_factory):
        """Verifica que get_status() retorna dict con estructura esperada"""
        agent = mock_agent_factory(agent_id="test_status")

        status = agent.get_status()

        assert isinstance(status, dict)
        assert status["id"] == "test_status"
        assert "name" in status
        assert "role" in status
        assert "level" in status
        assert "status" in status

    def test_execute_returns_default_response(self, mock_agent_factory):
        """Verifica que execute() retorna respuesta por defecto"""
        agent = mock_agent_factory()

        result = agent.execute("Test task")

        assert isinstance(result, dict)
        assert "content" in result
        assert result["success"] is True

    def test_execute_with_custom_return(self, mock_agent_factory):
        """Verifica que execute() usa valor personalizado"""
        custom_response = {"custom": "data", "code": "print('hello')"}
        agent = mock_agent_factory(execute_return_value=custom_response)

        result = agent.execute("Test task")

        assert result == custom_response

    def test_execute_with_side_effect_raises(self, mock_agent_factory):
        """Verifica que execute() lanza excepción configurada"""
        agent = mock_agent_factory(
            execute_side_effect=ValueError("Simulated error")
        )

        with pytest.raises(ValueError, match="Simulated error"):
            agent.execute("Test task")

    def test_can_execute_returns_true(self, mock_agent_factory):
        """Verifica que can_execute() retorna True por defecto"""
        agent = mock_agent_factory()

        assert agent.can_execute("any task") is True

    def test_update_status_is_mocked(self, mock_agent_factory):
        """Verifica que _update_status() es un mock que no falla"""
        agent = mock_agent_factory()

        # No debería lanzar excepción
        agent._update_status(AgentStatus.WORKING)
        agent._update_status.assert_called_once_with(AgentStatus.WORKING)


class TestPreconfiguredFixtures:
    """Tests para los fixtures preconfigurados"""

    def test_mock_agent_basic_has_defaults(self, mock_agent_basic):
        """Verifica que mock_agent_basic tiene valores por defecto"""
        assert mock_agent_basic.name == "Mock Agent"
        assert mock_agent_basic.level == AgentLevel.EXECUTION

    def test_mock_strategic_agent_has_correct_level(self, mock_strategic_agent):
        """Verifica nivel estratégico"""
        assert mock_strategic_agent.level == AgentLevel.STRATEGIC
        assert "Director" in mock_strategic_agent.role

    def test_mock_specialist_agent_has_correct_level(self, mock_specialist_agent):
        """Verifica nivel especialista"""
        assert mock_specialist_agent.level == AgentLevel.SPECIALIST
        assert "Backend" in mock_specialist_agent.role

    def test_mock_failing_agent_raises_on_execute(self, mock_failing_agent):
        """Verifica que el agente que falla realmente lanza excepción"""
        with pytest.raises(RuntimeError, match="Simulated agent failure"):
            mock_failing_agent.execute("any task")


class TestRegistryFixtures:
    """Tests para fixtures de AgentRegistry"""

    def test_empty_registry_is_truly_empty(self, empty_registry):
        """Verifica que empty_registry no tiene agentes"""
        assert len(empty_registry) == 0
        assert empty_registry.get_status_summary()["total"] == 0

    def test_populated_registry_has_agents(self, populated_registry):
        """Verifica que populated_registry tiene agentes registrados"""
        assert len(populated_registry) == 4

        summary = populated_registry.get_status_summary()
        assert summary["total"] == 4
        assert summary["by_level"]["STRATEGIC"] == 2
        assert summary["by_level"]["SPECIALIST"] == 1
        assert summary["by_level"]["EXECUTION"] == 1

    def test_populated_registry_can_find_agents(self, populated_registry):
        """Verifica búsqueda de agentes en registry poblado"""
        agent = populated_registry.get_agent_by_role("Project Director")
        assert agent is not None
        assert agent.level == AgentLevel.STRATEGIC


class TestConfigAndMemoryMocks:
    """Tests para mocks de configuración y memoria"""

    def test_mock_config_has_expected_attributes(self, mock_config):
        """Verifica que mock_config tiene atributos clave"""
        assert mock_config.agent_name == "TestBot"
        assert mock_config.autonomy_mode.value == "supervised"
        assert mock_config.preferred_languages == ["python"]

    def test_mock_config_methods_work(self, mock_config):
        """Verifica que métodos de mock_config funcionan"""
        prompt = mock_config.get_system_prompt()
        assert isinstance(prompt, str)

        can_exec = mock_config.can_execute_autonomously("read_file")
        assert isinstance(can_exec, bool)

    def test_mock_vector_memory_methods_return_expected(self, mock_vector_memory):
        """Verifica retornos de mock_vector_memory"""
        doc_id = mock_vector_memory.store("test content")
        assert doc_id == "mock_doc_id_123"

        results = mock_vector_memory.retrieve("query")
        assert results == []

    def test_mock_relational_memory_methods_return_expected(self, mock_relational_memory):
        """Verifica retornos de mock_relational_memory"""
        project = mock_relational_memory.get_project("any_id")
        assert project is not None
        assert project.name == "Mock Project"