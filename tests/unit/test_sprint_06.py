# devmind-core/tests/unit/test_sprint_06.py
"""
Tests unitarios para el Sprint 0.6: Auto-Mejora + Herramientas.
"""

# Mock para evitar requerir API keys en tests
import os

import pytest

os.environ["OPENAI_API_KEY"] = "sk-test-mock-key-for-testing-only"
os.environ["OLLAMA_HOST"] = "http://localhost:11434"

# También mockear crewai si es necesario
from unittest.mock import patch, MagicMock


# Patch global para CrewAI LLM
@pytest.fixture(autouse=True)
def mock_crewai_llm():
    """Mockea CrewAI LLM para evitar requerir API keys reales"""
    with patch('crewai.llm.LLM') as mock_llm:
        mock_instance = MagicMock()
        mock_instance.invoke.return_value = MagicMock(content='{"test": "data"}')
        mock_llm.return_value = mock_instance
        yield mock_llm


class TestToolBase:
    """Tests para BaseTool"""

    def test_tool_parameter_creation(self):
        """Test de creación de parámetro"""
        from core.tools.base import ToolParameter

        param = ToolParameter(
            name="test_param",
            type="str",
            description="Test parameter",
            required=True,
            default=None
        )

        assert param.name == "test_param"
        assert param.type == "str"
        assert param.required is True

    def test_tool_result_creation(self):
        """Test de creación de resultado"""
        from core.tools.base import ToolResult

        result = ToolResult(
            success=True,
            output="Test output",
            execution_time=1.234
        )

        assert result.success is True
        assert result.output == "Test output"
        assert result.execution_time == 1.234

    def test_tool_result_to_dict(self):
        """Test de serialización de resultado"""
        from core.tools.base import ToolResult

        result = ToolResult(success=True, output="test")
        result_dict = result.to_dict()

        assert "success" in result_dict
        assert "output" in result_dict


class TestToolRegistry:
    """Tests para ToolRegistry"""

    def test_singleton_pattern(self):
        """Test de patrón singleton"""
        from core.tools.registry import ToolRegistry

        registry1 = ToolRegistry()
        registry2 = ToolRegistry()

        assert registry1 is registry2

    def test_register_and_get(self):
        """Test de registro y obtención"""
        from core.tools.registry import ToolRegistry
        from core.tools.base import BaseTool, ToolDefinition, ToolResult

        registry = ToolRegistry()
        registry.reset()

        # Crear tool mock
        class TestTool(BaseTool):
            @property
            def definition(self):
                return ToolDefinition(
                    name="TestTool",
                    description="Test tool",
                    category="custom"
                )

            def execute(self, **kwargs):
                return ToolResult(success=True, output="test")

        tool = TestTool()
        registry.register(tool)

        retrieved = registry.get("TestTool")
        assert retrieved is tool

    def test_execute_tool(self):
        """Test de ejecución de herramienta"""
        from core.tools.registry import ToolRegistry
        from core.tools.base import BaseTool, ToolDefinition, ToolResult

        registry = ToolRegistry()
        registry.reset()

        class TestTool(BaseTool):
            @property
            def definition(self):
                return ToolDefinition(
                    name="TestTool",
                    description="Test tool",
                    category="custom",
                    parameters=[]
                )

            def execute(self, **kwargs):
                return ToolResult(success=True, output="executed")

        registry.register(TestTool())
        result = registry.execute("TestTool")

        assert result.success is True
        assert result.output == "executed"

    def test_list_tools(self):
        """Test de listado de herramientas"""
        from core.tools.registry import ToolRegistry
        from core.tools.base import BaseTool, ToolDefinition, ToolResult

        registry = ToolRegistry()
        registry.reset()

        class TestTool(BaseTool):
            @property
            def definition(self):
                return ToolDefinition(
                    name="TestTool",
                    description="Test tool",
                    category="custom"
                )

            def execute(self, **kwargs):
                return ToolResult(success=True, output="test")

        registry.register(TestTool())
        tools = registry.list_tools()

        assert len(tools) >= 1


class TestToolBuilder:
    """Tests para ToolBuilderAgent"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para el LLM del agente"""
        with patch('core.agents.base.CrewAIAgent') as mock_crew:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = MagicMock(content='{"name": "TestTool"}')
            mock_crew.return_value = mock_agent
            yield mock_agent

    def test_tool_builder_creation(self, mock_llm):
        """Test de creación de ToolBuilder"""
        from core.self_improvement.tool_builder import ToolBuilderAgent

        agent = ToolBuilderAgent()

        assert agent.name == "Tool Builder"
        assert agent.tools_created == 0

    def test_parse_json_response(self, mock_llm):
        """Test de parseo de JSON"""
        from core.self_improvement.tool_builder import ToolBuilderAgent

        agent = ToolBuilderAgent()

        # JSON válido
        json_str = '{"key": "value"}'
        result = agent._parse_json_response(json_str)
        assert result == {"key": "value"}

        # JSON inválido
        result = agent._parse_json_response("not json")
        assert "raw" in result


class TestAgentCreator:
    """Tests para AgentCreatorAgent"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para el LLM del agente"""
        with patch('core.agents.base.CrewAIAgent') as mock_crew:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = MagicMock(content='{"name": "TestAgent"}')
            mock_crew.return_value = mock_agent
            yield mock_agent

    def test_agent_creator_creation(self, mock_llm):
        """Test de creación de AgentCreator"""
        from core.self_improvement.agent_creator import AgentCreatorAgent

        agent = AgentCreatorAgent()

        assert agent.name == "Agent Creator"
        assert agent.agents_created == 0

    def test_validate_agent_config(self, mock_llm):
        """Test de validación de configuración"""
        from core.self_improvement.agent_creator import AgentCreatorAgent

        agent = AgentCreatorAgent()

        # Configuración válida
        valid_config = {
            "name": "TestAgent",
            "role": "Tester",
            "goal": "Test things",
            "level": "EXECUTION"
        }
        result = agent._validate_agent(valid_config)
        assert result["valid"] is True

        # Configuración inválida (faltan campos)
        invalid_config = {"name": "TestAgent"}
        result = agent._validate_agent(invalid_config)
        assert result["valid"] is False


class TestLanguageLearner:
    """Tests para LanguageLearnerAgent"""

    @pytest.fixture
    def mock_llm(self):
        """Mock para el LLM del agente"""
        with patch('core.agents.base.CrewAIAgent') as mock_crew:
            mock_agent = MagicMock()
            mock_agent.invoke.return_value = MagicMock(content='{"name": "Python"}')
            mock_crew.return_value = mock_agent
            yield mock_agent

    def test_language_learner_creation(self, mock_llm):
        """Test de creación de LanguageLearner"""
        from core.self_improvement.language_learner import LanguageLearnerAgent

        agent = LanguageLearnerAgent()

        assert agent.name == "Language Learner"
        assert agent.languages_learned == 0

    def test_set_memory(self, mock_llm):
        """Test de establecimiento de memoria"""
        from core.self_improvement.language_learner import LanguageLearnerAgent

        agent = LanguageLearnerAgent()
        mock_memory = MagicMock()

        agent.set_memory(mock_memory)
        assert agent.memory is mock_memory


class TestCapabilityValidator:
    """Tests para CapabilityValidator"""

    # ... tests existentes ...

    def test_validate_tool_structure(self):
        """Test de validación de estructura de tool"""
        from core.self_improvement.capability_validator import CapabilityValidator

        validator = CapabilityValidator()

        # Código válido - debe incluir todos los elementos requeridos
        valid_code = '''"""Test Tool"""
from core.tools.base import BaseTool, ToolDefinition, ToolResult

class TestTool(BaseTool):
    @property
    def definition(self) -> ToolDefinition:
        return ToolDefinition(
            name="TestTool",
            description="Test tool",
            category="custom"
        )

    def execute(self, **kwargs) -> ToolResult:
        return ToolResult(success=True, output="test")
'''
        result = validator._validate_tool_structure(valid_code, "TestTool")
        assert result["passed"] is True, f"Errors: {result.get('errors', [])}"

        # Código inválido - falta herencia de BaseTool
        invalid_code = '''
class TestTool:
    def execute(self):
        pass
'''
        result = validator._validate_tool_structure(invalid_code, "TestTool")
        assert result["passed"] is False


class TestAddonRegistry:
    """Tests para AddonRegistry"""

    def test_singleton_pattern(self):
        """Test de patrón singleton"""
        from core.addons.registry import AddonRegistry

        registry1 = AddonRegistry()
        registry2 = AddonRegistry()

        assert registry1 is registry2

    def test_register_and_get(self):
        """Test de registro y obtención"""
        from core.addons.registry import AddonRegistry
        from core.addons.base import BaseAddon, AddonManifest

        registry = AddonRegistry()
        registry.reset()

        # Crear addon mock
        class TestAddon(BaseAddon):
            @property
            def manifest(self):
                return AddonManifest(
                    name="TestAddon",
                    version="1.0.0",
                    description="Test addon",
                    author="Test"
                )

            def activate(self):
                return True

            def deactivate(self):
                return True

        addon = TestAddon()
        registry.register(addon)

        retrieved = registry.get("TestAddon")
        assert retrieved is addon

    def test_activate_deactivate(self):
        """Test de activación/desactivación"""
        from core.addons.registry import AddonRegistry
        from core.addons.base import BaseAddon, AddonManifest

        registry = AddonRegistry()
        registry.reset()

        class TestAddon(BaseAddon):
            @property
            def manifest(self):
                return AddonManifest(
                    name="TestAddon",
                    version="1.0.0",
                    description="Test addon",
                    author="Test"
                )

            def activate(self):
                self.active = True
                return True

            def deactivate(self):
                self.active = False
                return True

        addon = TestAddon()
        registry.register(addon)

        # Activar
        registry.activate("TestAddon")
        assert addon.active is True

        # Desactivar
        registry.deactivate("TestAddon")
        assert addon.active is False


class TestAddonLoader:
    """Tests para AddonLoader"""

    def test_loader_creation(self):
        """Test de creación de loader"""
        from core.addons.loader import AddonLoader

        loader = AddonLoader()

        assert loader.registry is not None
        assert len(loader._watch_paths) == 0

    def test_watch_directory(self):
        """Test de monitoreo de directorio"""
        from core.addons.loader import AddonLoader
        from pathlib import Path

        loader = AddonLoader()
        test_path = Path("/tmp/test_addons")

        loader.watch_directory(test_path)

        assert test_path in loader._watch_paths


class TestCLICommands:
    """Tests para comandos CLI"""

    def test_tools_command_exists(self):
        """Test de existencia de comando tools"""
        from cli.commands.tools import tools_group
        assert tools_group is not None

    def test_addons_command_exists(self):
        """Test de existencia de comando addons"""
        from cli.commands.addons import addons_group
        assert addons_group is not None
