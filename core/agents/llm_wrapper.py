# devmind-core/core/agents/llm_wrapper.py
"""
Wrapper compatible para LLMs de CrewAI 1.9.3.
Proporciona interfaz LangChain-compatible (invoke/stream) para CrewLLM.
"""
import logging
from typing import Any, Optional, AsyncIterator, Iterator
import urllib.request
import json

logger = logging.getLogger(__name__)


class CrewLLMWrapper:
    """
    Wrapper que adapta CrewLLM a la interfaz de LangChain.

    Proporciona:
    - invoke(content) -> response con atributo .content
    - stream(content) -> Iterator de chunks
    """

    def __init__(self, crew_llm: Any):
        """
        Inicializa el wrapper.

        Args:
            crew_llm: Instancia de crewai.LLM
        """
        self._crew_llm = crew_llm

    def invoke(self, prompt: str, **kwargs) -> Any:
        """
        Invoca el LLM con un prompt.

        Args:
            prompt: Texto del prompt
            **kwargs: Argumentos adicionales

        Returns:
            Objeto con atributo .content (compatible con LangChain)
        """
        try:
            # Fallback directo a Ollama API para máxima compatibilidad
            return self._call_ollama_direct(prompt, **kwargs)

        except Exception as e:
            logger.error(f"Error invoking CrewLLM: {e}")
            return _LangChainResponse(content=f"⚠️ Error: {e}")

    def _call_ollama_direct(self, prompt: str, **kwargs) -> Any:
        """Conexión directa a Ollama API"""
        ollama_url = getattr(self._crew_llm, 'base_url', 'http://localhost:11434')
        model = getattr(self._crew_llm, 'model', 'llama3.2:3b')
        temperature = getattr(self._crew_llm, 'temperature', 0.7)

        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        req = urllib.request.Request(
            f"{ollama_url}/api/generate",
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json'}
        )

        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            content = result.get('response', '')
            return _LangChainResponse(content=content)

    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream de respuesta token por token"""
        try:
            response = self.invoke(prompt, **kwargs)
            content = response.content if hasattr(response, 'content') else str(response)

            # Yieldear por palabras para simular streaming
            words = content.split()
            for i in range(0, len(words), 3):
                yield ' '.join(words[i:i + 3]) + ' '

        except Exception as e:
            logger.error(f"Error streaming: {e}")
            yield f"⚠️ Error: {e}"

    async def ainvoke(self, prompt: str, **kwargs) -> Any:
        """Versión async de invoke"""
        return self.invoke(prompt, **kwargs)

    async def astream(self, prompt: str, **kwargs) -> AsyncIterator[str]:
        """Versión async de stream"""
        for chunk in self.stream(prompt, **kwargs):
            yield chunk

    def __getattr__(self, name: str):
        """Delegar otros atributos al LLM original"""
        return getattr(self._crew_llm, name)


class _LangChainResponse:
    """Respuesta compatible con LangChain"""

    def __init__(self, content: str):
        self.content = content
        self.text = content

    def __str__(self) -> str:
        return self.content

    def __repr__(self) -> str:
        return f"Response(content={self.content[:50]}...)"