# devmind-core/cli/streaming.py
"""
Soporte de streaming para respuestas en tiempo real del agente.

Permite mostrar la generación de texto token por token,
similar a como lo hace ChatGPT o Claude.
"""

import asyncio
from typing import AsyncGenerator, Dict, Any, Optional, Callable

from rich.console import Console

console = Console()


class StreamingResponse:
    """
    Maneja la visualización de respuestas en streaming del agente.

    Características:
    - Muestra texto token por token
    - Indicadores de estado (pensando, escribiendo, etc.)
    - Soporte para múltiples tipos de contenido (texto, código, archivos)
    - Cancelación segura con Ctrl+C
    """

    def __init__(
            self,
            agent_name: str = "DevMind",
            show_thinking: bool = True,
            color: str = "green"
    ):
        self.agent_name = agent_name
        self.show_thinking = show_thinking
        self.color = color
        self.current_text = ""
        self.is_complete = False
        self._cancel_requested = False

    async def stream(
            self,
            response_generator: AsyncGenerator[Dict[str, Any], None],
            on_token: Optional[Callable[[str], None]] = None,
            on_complete: Optional[Callable[[Dict[str, Any]], None]] = None
    ) -> Dict[str, Any]:
        """
        Muestra una respuesta en streaming mientras se genera.

        Args:
            response_generator: Generador asíncrono que yield tokens
            on_token: Callback por cada token recibido
            on_complete: Callback cuando la respuesta está completa

        Returns:
            Resultado completo de la respuesta
        """
        self.current_text = ""
        self.is_complete = False

        # Mostrar indicador de "pensando"
        if self.show_thinking:
            with console.status(f"[bold {self.color}]{self.agent_name} está pensando...[/]", spinner="dots"):
                # Esperar primer token
                try:
                    first_chunk = await response_generator.__anext__()
                except StopAsyncIteration:
                    return {"content": "", "complete": True}

            # Mostrar panel de respuesta
            self._display_start()

        # Procesar chunks
        final_result = None

        try:
            # Procesar primer chunk
            final_result = await self._process_chunk(first_chunk, on_token)

            # Procesar chunks restantes
            async for chunk in response_generator:
                if self._cancel_requested:
                    console.print(f"\n[yellow]⚠️  Respuesta cancelada por el usuario[/]")
                    break

                final_result = await self._process_chunk(chunk, on_token)

            self.is_complete = True
            self._display_complete()

            if on_complete and final_result:
                on_complete(final_result)

            return final_result or {"content": self.current_text, "complete": True}

        except asyncio.CancelledError:
            console.print(f"\n[yellow]⚠️  Respuesta cancelada[/]")
            return {"content": self.current_text, "cancelled": True}
        except Exception as e:
            console.print(f"\n[red]❌ Error: {str(e)}[/]")
            return {"content": self.current_text, "error": str(e)}

    def _display_start(self) -> None:
        """Muestra el inicio de la respuesta del agente"""
        console.print(f"\n[bold {self.color}]{self.agent_name}:[/bold {self.color}] ", end="")

    def _display_complete(self) -> None:
        """Muestra indicador de respuesta completa"""
        console.print()  # Nueva línea al final

    async def _process_chunk(
            self,
            chunk: Dict[str, Any],
            on_token: Optional[Callable[[str], None]] = None
    ) -> Dict[str, Any]:
        """Procesa un chunk de la respuesta"""
        chunk_type = chunk.get("type", "token")

        if chunk_type == "token":
            token = chunk.get("token", "")
            self.current_text += token
            console.print(token, end="", markup=False)

            if on_token:
                on_token(token)

        elif chunk_type == "status":
            status_msg = chunk.get("message", "")
            console.print(f"\n[dim]{status_msg}[/dim]")

        elif chunk_type == "file":
            file_info = chunk.get("file", {})
            console.print(f"\n[bold blue]📁 Archivo creado:[/bold blue] {file_info.get('path', 'unknown')}")

        elif chunk_type == "error":
            error_msg = chunk.get("error", "")
            console.print(f"\n[red]❌ Error:[/red] {error_msg}")

        elif chunk_type == "complete":
            # Metadata final
            pass

        return chunk

    def cancel(self) -> None:
        """Solicita cancelación del streaming"""
        self._cancel_requested = True

    def reset(self) -> None:
        """Resetea el estado para nueva respuesta"""
        self.current_text = ""
        self.is_complete = False
        self._cancel_requested = False


class TypingEffect:
    """
    Efecto de tipeo para mostrar texto caracter por caracter.

    Más lento que streaming real, pero útil para mensajes cortos.
    """

    def __init__(self, delay: float = 0.02):
        self.delay = delay

    async def display(self, text: str, prefix: str = "") -> None:
        """Muestra texto con efecto de tipeo"""
        if prefix:
            console.print(prefix, end="")

        for char in text:
            console.print(char, end="", markup=False)
            await asyncio.sleep(self.delay)

        console.print()  # Nueva línea al final

    async def display_lines(self, lines: list, prefix: str = "") -> None:
        """Muestra múltiples líneas con efecto de tipeo"""
        for i, line in enumerate(lines):
            if i > 0:
                await asyncio.sleep(0.1)  # Pequeña pausa entre líneas
            await self.display(line, prefix if i == 0 else "")


async def stream_agent_response(
        orchestrator,
        message: str,
        session_id: str = None,
        agent_name: str = "DevMind"
) -> Dict[str, Any]:
    """
    Función helper para hacer streaming de respuesta del orchestrator.

    Args:
        orchestrator: Instancia de DevMindOrchestrator
        message: Mensaje del usuario
        session_id: ID de sesión para contexto
        agent_name: Nombre a mostrar

    Returns:
        Resultado completo de la respuesta
    """
    streaming = StreamingResponse(agent_name=agent_name)

    async def response_generator():
        """Generador que convierte la respuesta del orchestrator en chunks"""
        try:
            result = await orchestrator.process_message(
                message=message,
                session_id=session_id
            )

            # Convertir resultado en chunks de streaming
            content = result.get("response", "")

            # Simular streaming token por token (en producción, el orchestrator debería ser nativamente streaming)
            words = content.split(" ")
            for i, word in enumerate(words):
                token = word + (" " if i < len(words) - 1 else "")
                yield {"type": "token", "token": token}
                await asyncio.sleep(0.02)  # Pequeña pausa entre palabras

            # Metadata final
            if result.get("files_modified"):
                for file in result["files_modified"]:
                    yield {"type": "file", "file": file}

            yield {"type": "complete"}

        except Exception as e:
            yield {"type": "error", "error": str(e)}

    return await streaming.stream(response_generator)