# devmind-core/tests/conftest.py
"""
Fixtures globales de pytest para DevMind Core.

Este archivo se carga automáticamente por pytest y proporciona
fixtures reutilizables para todos los tests del proyecto.
"""

from typing import Any
from unittest.mock import Mock

import pytest

from core.agents.base import AgentLevel, AgentStatus


@pytest.fixture
def mock_agent_factory():
    """
    Factory para crear mocks de BaseAgent bien configurados.

    Uso:
        agent = mock_agent_factory(
            agent_id="test_123",
            role="Test Role",
            level=AgentLevel.EXECUTION
        )
    """

    def _create_mock_agent(
            agent_id: str = "mock_agent_001",
            name: str = "Mock Agent",
            role: str = "Test Role",
            level: AgentLevel = AgentLevel.EXECUTION,
            status: AgentStatus = AgentStatus.IDLE,
            tasks_completed: int = 0,
            tasks_failed: int = 0,
            execute_return_value: Any = None,
            execute_side_effect: Exception = None
    ):
        """Crea un mock de agente con configuración personalizada"""

        mock_agent = Mock(spec=[
            'id', 'name', 'role', 'level', 'status',
            'tasks_completed', 'tasks_failed', 'last_active',
            'execute', 'can_execute', 'get_status',
            '_update_status', '_create_crew_agent', 'llm', 'crew_agent'
        ])

        # Atributos básicos
        mock_agent.id = agent_id
        mock_agent.name = name
        mock_agent.role = role
        mock_agent.level = level
        mock_agent.status = status
        mock_agent.tasks_completed = tasks_completed
        mock_agent.tasks_failed = tasks_failed
        mock_agent.last_active = None

        # Método get_status()
        def _get_status():
            return {
                "id": mock_agent.id,
                "name": mock_agent.name,
                "role": mock_agent.role,
                "level": getattr(level, 'value', level),
                "status": getattr(status, 'value', status),
                "tasks_completed": mock_agent.tasks_completed,
                "tasks_failed": mock_agent.tasks_failed,
                "last_active": mock_agent.last_active
            }

        mock_agent.get_status = Mock(side_effect=_get_status)

        # Método execute()
        if execute_side_effect:
            mock_agent.execute = Mock(side_effect=execute_side_effect)
        else:
            mock_agent.execute = Mock(return_value=execute_return_value or {
                "content": f"Response from {name}",
                "success": True
            })

        # Método can_execute()
        mock_agent.can_execute = Mock(return_value=True)

        # Método _update_status() (no hace nada en mock)
        mock_agent._update_status = Mock()

        return mock_agent

    return _create_mock_agent


@pytest.fixture
def mock_agent_basic(mock_agent_factory):
    """Mock de agente básico con configuración por defecto"""
    return mock_agent_factory()


@pytest.fixture
def mock_strategic_agent(mock_agent_factory):
    """Mock de agente de nivel estratégico"""
    return mock_agent_factory(
        name="Strategic Mock",
        role="Project Director",
        level=AgentLevel.STRATEGIC,
        execute_return_value={
            "plan": {"phases": 3, "estimated_hours": 120},
            "viability": {"score": 85}
        }
    )


@pytest.fixture
def mock_specialist_agent(mock_agent_factory):
    """Mock de agente especialista"""
    return mock_agent_factory(
        name="Specialist Mock",
        role="Backend Specialist",
        level=AgentLevel.SPECIALIST,
        execute_return_value={
            "code": {"files": ["models.py", "views.py"]},
            "tests": {"coverage": 95}
        }
    )


@pytest.fixture
def mock_execution_agent(mock_agent_factory):
    """Mock de agente de ejecución"""
    return mock_agent_factory(
        name="Execution Mock",
        role="Coder Agent",
        level=AgentLevel.EXECUTION,
        execute_return_value={
            "output": "Code generated successfully",
            "files_created": ["main.py"]
        }
    )


@pytest.fixture
def mock_failing_agent(mock_agent_factory):
    """Mock de agente que falla en execute()"""
    return mock_agent_factory(
        name="Failing Mock",
        execute_side_effect=RuntimeError("Simulated agent failure")
    )


@pytest.fixture
def empty_registry():
    """Registry vacío y reseteado para tests aislados"""
    from core.agents.registry import AgentRegistry

    registry = AgentRegistry()
    registry.reset()
    return registry


@pytest.fixture
def populated_registry(empty_registry, mock_agent_factory):
    """Registry con agentes de ejemplo para tests"""
    agents = [
        mock_agent_factory(agent_id="dir_001", role="Project Director", level=AgentLevel.STRATEGIC),
        mock_agent_factory(agent_id="arch_001", role="Architect Principal", level=AgentLevel.STRATEGIC),
        mock_agent_factory(agent_id="backend_001", role="Backend Specialist", level=AgentLevel.SPECIALIST),
        mock_agent_factory(agent_id="coder_001", role="Coder Agent", level=AgentLevel.EXECUTION),
    ]

    for agent in agents:
        empty_registry.register(agent)

    return empty_registry


@pytest.fixture(autouse=True)
def reset_singletons():
    """Resetea singletons después de cada test para aislamiento"""
    yield
    # Resetear AgentRegistry después de cada test
    try:
        from core.agents.registry import AgentRegistry
        if AgentRegistry._instance:
            AgentRegistry._instance.reset()
    except ImportError:
        pass  # Ignorar si el módulo no está disponible


@pytest.fixture
def mock_config():
    """Mock de AgentConfig con valores por defecto seguros"""
    from unittest.mock import MagicMock
    from core.config.schema import AutonomyMode, PersonalityType, LearningMode

    config = MagicMock()
    config.agent_name = "TestBot"
    config.personality = PersonalityType.PROFESSIONAL
    config.communication_style = "concise"
    config.autonomy_mode = AutonomyMode.SUPERVISED
    config.max_file_write_without_confirm = 5
    config.allow_internet = False
    config.allow_email = False
    config.allow_self_improvement = True
    config.sandbox_enabled = True
    config.preferred_languages = ["python"]
    config.learning_mode = LearningMode.BALANCED
    config.enable_all_agents = True
    config.priority_agents = []
    config.git_config = None

    # Método helper
    config.get_system_prompt.return_value = "Test system prompt"
    config.can_execute_autonomously.return_value = False

    return config


@pytest.fixture
def mock_vector_memory():
    """Mock de VectorMemory para tests sin ChromaDB"""
    mock = Mock()
    mock.store.return_value = "mock_doc_id_123"
    mock.retrieve.return_value = []
    mock.store_code_snapshot.return_value = "mock_code_id"
    mock.store_decision.return_value = "mock_decision_id"
    mock.store_conversation.return_value = "mock_conv_id"
    mock.get_project_knowledge.return_value = ""
    mock.get_stats.return_value = {"total_documents": 0}
    return mock


@pytest.fixture
def mock_relational_memory():
    """Mock de RelationalMemory para tests sin PostgreSQL"""
    mock = Mock()

    # Mock para proyectos
    mock_project = Mock()
    mock_project.id = "mock_project_uuid"
    mock_project.name = "Mock Project"
    mock.get_project.return_value = mock_project
    mock.create_project.return_value = mock_project

    # Mock para sesiones
    mock_session = Mock()
    mock_session.id = "mock_session_uuid"
    mock.create_conversation_session.return_value = mock_session

    # Métodos que no hacen nada pero no fallan
    mock.add_message.return_value = Mock()
    mock.search.return_value = {}
    mock.get_project_metrics.return_value = {}

    return mock