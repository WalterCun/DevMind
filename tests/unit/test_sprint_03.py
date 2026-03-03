# devmind-core/tests/unit/test_sprint_03.py
"""
Tests unitarios para el Sprint 0.3: Módulos Base del Core.
Actualizado para usar fixtures de conftest.py
"""

import pytest

from core.agents import AgentLevel
from core.utils.helpers import safe_get, parse_json_safe


class TestHelpers:
    """Tests para funciones helper"""

    def test_safe_get_with_none(self):
        assert safe_get(None, "attr", "default") == "default"

    def test_safe_get_with_valid_attr(self):
        class Obj:
            value = 42

        assert safe_get(Obj(), "value", "default") == 42

    def test_safe_get_with_missing_attr(self):
        class Obj:
            pass

        assert safe_get(Obj(), "missing", "fallback") == "fallback"

    def test_parse_json_safe_with_valid_json(self):
        result = parse_json_safe('{"key": "value"}')
        assert result == {"key": "value"}

    def test_parse_json_safe_with_text_block(self):
        text = 'Aquí hay JSON: {"test": 123} y más texto'
        result = parse_json_safe(text)
        assert result == {"test": 123}

    def test_parse_json_safe_with_invalid_returns_default(self):
        result = parse_json_safe('not json at all', default={"fallback": True})
        assert result == {"fallback": True}


class TestAgentRegistry:
    """Tests para AgentRegistry usando fixtures"""

    def test_singleton_pattern(self):
        """Verifica que AgentRegistry es Singleton"""
        from core.agents.registry import AgentRegistry

        reg1 = AgentRegistry()
        reg2 = AgentRegistry()

        assert reg1 is reg2

    def test_register_and_get_with_fixture(self, empty_registry, mock_agent_factory):
        """Verifica registro y recuperación usando fixtures"""
        # Crear agente con factory
        agent = mock_agent_factory(
            agent_id="test_agent_123",
            role="Test Role",
            level=AgentLevel.EXECUTION
        )

        # Registrar y verificar
        agent_id = empty_registry.register(agent)

        assert agent_id == "test_agent_123"
        assert empty_registry.get_agent("test_agent_123") is agent
        assert empty_registry.get_agent_by_role("test role") is agent

    def test_get_status_summary_empty(self, empty_registry):
        """Verifica resumen con registry vacío"""
        summary = empty_registry.get_status_summary()

        assert summary["total"] == 0
        assert summary["initialized"] is False

    def test_populated_registry_summary(self, populated_registry):
        """Verifica resumen con registry poblado (usa fixture)"""
        summary = populated_registry.get_status_summary()

        assert summary["total"] == 4
        assert summary["by_level"]["STRATEGIC"] == 2


@pytest.mark.requires_ollama
@pytest.mark.skip(reason="Requires Ollama and ChromaDB running")
class TestVectorMemory:
    """Tests para VectorMemory (requieren servicios externos)"""

    def test_store_and_retrieve(self):
        from core.memory.vector_store import VectorMemory, MemoryCategory

        memory = VectorMemory(project_id="test_project_for_ci")
        doc_id = memory.store("Test content for CI", category=MemoryCategory.GENERAL)

        results = memory.retrieve("Test content", limit=1)
        assert len(results) >= 1
        assert "Test content" in results[0]["content"]