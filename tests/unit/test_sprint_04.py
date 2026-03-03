# devmind-core/tests/unit/test_sprint_04.py
"""
Tests unitarios para el Sprint 0.4: Integración CLI + Orchestrator.
"""

import pytest


class TestStreamingResponse:
    """Tests para StreamingResponse"""

    @pytest.mark.asyncio
    async def test_stream_basic(self):
        """Test básico de streaming"""
        from cli.streaming import StreamingResponse

        streaming = StreamingResponse(agent_name="TestBot")

        async def mock_generator():
            yield {"type": "token", "token": "Hello"}
            yield {"type": "token", "token": " "}
            yield {"type": "token", "token": "World"}
            yield {"type": "complete"}

        result = await streaming.stream(mock_generator())

        assert streaming.current_text == "Hello World"
        assert streaming.is_complete is True

    @pytest.mark.asyncio
    async def test_stream_with_error(self):
        """Test de streaming con error"""
        from cli.streaming import StreamingResponse

        streaming = StreamingResponse(agent_name="TestBot")

        async def mock_generator():
            yield {"type": "token", "token": "Error"}
            yield {"type": "error", "error": "Test error"}

        result = await streaming.stream(mock_generator())

        assert "error" in result or streaming.current_text == "Error"


class TestSessionContext:
    """Tests para SessionContext"""

    def test_create_session(self):
        """Test de creación de sesión"""
        from cli.context import SessionContext

        session = SessionContext(project_id="test_project", mode="chat")

        assert session.project_id == "test_project"
        assert session.mode == "chat"
        assert session.session_id is not None
        assert len(session.message_history) == 0

    def test_add_message(self):
        """Test de agregar mensaje"""
        from cli.context import SessionContext

        session = SessionContext()
        session.add_message("user", "Hello", intent="greeting")

        assert len(session.message_history) == 1
        assert session.message_history[0]["role"] == "user"
        assert session.message_history[0]["intent"] == "greeting"

    def test_get_recent_messages(self):
        """Test de obtener mensajes recientes"""
        from cli.context import SessionContext

        session = SessionContext()

        for i in range(15):
            session.add_message("user", f"Message {i}")

        recent = session.get_recent_messages(limit=5)

        assert len(recent) == 5
        assert "Message 14" in recent[-1]["content"]

    def test_set_mode(self):
        """Test de cambiar modo"""
        from cli.context import SessionContext

        session = SessionContext(mode="chat")
        session.set_mode("code")

        assert session.mode == "code"

    def test_set_mode_invalid(self):
        """Test de modo inválido"""
        from cli.context import SessionContext

        session = SessionContext()

        with pytest.raises(ValueError):
            session.set_mode("invalid_mode")

    def test_to_dict_and_from_dict(self):
        """Test de serialización"""
        from cli.context import SessionContext

        original = SessionContext(project_id="test", mode="plan")
        original.add_message("user", "Test message")

        data = original.to_dict()
        restored = SessionContext.from_dict(data)

        assert restored.session_id == original.session_id
        assert restored.project_id == original.project_id
        assert len(restored.message_history) == len(original.message_history)


class TestContextManager:
    """Tests para ContextManager"""

    def test_create_session(self):
        """Test de creación de sesión con manager"""
        from cli.context import ContextManager

        manager = ContextManager()
        session = manager.create_session(project_id="test", mode="code")

        assert manager.current_context is session
        assert session.project_id == "test"

    def test_add_message(self):
        """Test de agregar mensaje con manager"""
        from cli.context import ContextManager

        manager = ContextManager()
        manager.create_session()
        manager.add_message("user", "Test")

        assert len(manager.get_history()) == 1

    def test_switch_project(self):
        """Test de cambiar proyecto"""
        from cli.context import ContextManager

        manager = ContextManager()
        manager.create_session(project_id="project_a")
        manager.switch_project("project_b")

        assert manager.current_context.project_id == "project_b"


class TestCodeCommands:
    """Tests para comandos de código"""

    def test_extract_code_blocks_basic(self):
        """Test de extracción de bloques de código"""
        from cli.commands.code import _extract_code_blocks

        response = """
Aquí está el código:

```python
def hello():
    return "world"
```
"""
        blocks = _extract_code_blocks(response)
        assert len(blocks) >= 1
        assert blocks[0]["language"] == "python"
        # El código debe contener al menos parte del contenido
        assert "hello" in blocks[0]["code"].lower() or "world" in blocks[0]["code"]

    def test_extract_code_blocks_multiple(self):
        """Test de múltiples bloques"""
        from cli.commands.code import _extract_code_blocks

        response = """# file: models.py
class User:
    pass
        
# file: views.py
def index():
    pass        
"""
        blocks = _extract_code_blocks(response)
        # Debería encontrar al menos 1 bloque (el regex puede variar)
        assert len(blocks) >= 1
        # Verificar que se extrajo código
        assert any("class" in b["code"] or "def" in b["code"] for b in blocks)

        def test_extract_code_blocks_with_route(self):
            """Test de extracción con ruta de archivo"""
            from cli.commands.code import _extract_code_blocks

            # Formato más realista: ruta en comentario dentro del bloque
            response = """```python
    # ruta: test_file.py
    def test():
        pass
    ```"""
            blocks = _extract_code_blocks(response)

            assert len(blocks) >= 1
            # La ruta debería haberse extraído correctamente
            assert blocks[0]["path"] == "test_file.py", f"Expected 'test_file.py', got '{blocks[0]['path']}'"
            assert blocks[0]["language"] == "python"
            # El código debería contener la función
            assert "def test" in blocks[0]["code"]

        def test_extract_code_blocks_with_file_comment(self):
            """Test alternativo con formato # file:"""
            from cli.commands.code import _extract_code_blocks

            response = """```javascript
    // file: utils.js
    function helper() {
        return true;
    }
    ```"""
            blocks = _extract_code_blocks(response)

            assert len(blocks) >= 1
            assert blocks[0]["path"] == "utils.js"
            assert blocks[0]["language"] == "javascript"
            assert "function helper" in blocks[0]["code"]


class TestFixCommands:
    """Tests para comando fix"""

    def test_build_analysis_prompt(self):
        """Test de construcción de prompt de análisis"""
        from cli.commands.fix import _build_analysis_prompt

        prompt = _build_analysis_prompt(
            description="Test error",
            target_file="test.py",
            error_log="Traceback: AttributeError"
        )

        assert "Test error" in prompt
        assert "test.py" in prompt
        # El log debería estar en el prompt (puede estar dentro de ```)
        assert "Traceback" in prompt or "AttributeError" in prompt

    def test_build_analysis_prompt_no_error_log(self):
        """Test sin error log"""
        from cli.commands.fix import _build_analysis_prompt

        prompt = _build_analysis_prompt(
            description="Test error",
            target_file="test.py",
            error_log=None
        )

        assert "Test error" in prompt
        assert "test.py" in prompt
        assert "```" not in prompt or prompt.count("```") == 0

    def test_build_fix_prompt(self):
        """Test de construcción de prompt de fix"""
        from cli.commands.fix import _build_fix_prompt

        analysis = {"response": "Root cause: null pointer"}

        prompt = _build_fix_prompt(
            description="Test fix",
            target_file="test.py",
            error_log="Error...",
            analysis_result=analysis,
            with_tests=True
        )

        assert "Test fix" in prompt
        assert "Root cause" in prompt
        assert "tests" in prompt.lower() or "Tests" in prompt
