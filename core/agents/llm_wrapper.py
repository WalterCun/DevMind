# devmind-core/core/agents/llm_wrapper.py
"""
Wrapper compatible para LLMs de CrewAI 1.9.3.
Proporciona interfaz LangChain-compatible (invoke/stream) para CrewLLM.
"""

import logging
from typing import Any, Optional, AsyncIterator, Iterator

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
            # CrewAI 1.9.3: intentar diferentes métodos para generar respuestas
            response_content = None

            # Opción 1: Si tiene método generate/complete
            if hasattr(self._crew_llm, 'generate'):
                response_content = self._crew_llm.generate(prompt, **kwargs)
            elif hasattr(self._crew_llm, 'complete'):
                response_content = self._crew_llm.complete(prompt, **kwargs)
            elif hasattr(self._crew_llm, '__call__'):
                # Algunos wrappers permiten llamada directa
                response_content = self._crew_llm(prompt, **kwargs)
            else:
                # Fallback: intentar acceder al cliente subyacente
                if hasattr(self._crew_llm, '_client'):
                    client = self._crew_llm._client
                    if hasattr(client, 'create'):
                        response = client.create(
                            model=getattr(self._crew_llm, 'model', 'llama3'),
                            messages=[{"role": "user", "content": prompt}],
                            **kwargs
                        )
                        response_content = response.choices[0].message.content
                    elif hasattr(client, 'chat'):
                        response = client.chat.completions.create(
                            messages=[{"role": "user", "content": prompt}],
                            **kwargs
                        )
                        response_content = response.choices[0].message.content

            # Si aún no tenemos respuesta, usar fallback directo a Ollama
            if response_content is None:
                response_content = self._call_ollama_direct(prompt)

            # Normalizar respuesta a formato LangChain
            if isinstance(response_content, str):
                return _LangChainResponse(content=response_content)
            elif hasattr(response_content, 'content'):
                return response_content
            else:
                return _LangChainResponse(content=str(response_content))

        except Exception as e:
            logger.error(f"Error invoking CrewLLM: {e}")
            return _LangChainResponse(content=f"⚠️ Error: {e}")

    def _call_ollama_direct(self, prompt: str) -> str:
        """Fallback: conexión directa a Ollama API con manejo de errores"""
        import urllib.request, json, urllib.error

        ollama_url = getattr(self._crew_llm, 'base_url', 'http://localhost:11434')
        model = getattr(self._crew_llm, 'model', 'qwen3-coder:30b')  # ← Default correcto
        temperature = getattr(self._crew_llm, 'temperature', 0.7)

        data = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature}
        }

        try:
            req = urllib.request.Request(
                f"{ollama_url}/api/generate",
                data=json.dumps(data).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )

            with urllib.request.urlopen(req, timeout=120) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('response', '')

        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.error(f"Model '{model}' not found in Ollama. Available models: run 'ollama list'")
                return f"⚠️ Error: El modelo '{model}' no está disponible. Verifica con 'ollama list'."
            raise
        except Exception as e:
            logger.error(f"Error calling Ollama API: {e}")
            return f"⚠️ Error de conexión a Ollama: {e}"

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