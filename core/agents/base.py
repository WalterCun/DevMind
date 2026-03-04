# devmind-core/core/agents/base.py
"""
Clase base para todos los agentes de DevMind Core.

Compatible con:
- CrewAI 1.9.3+
- langchain-ollama 1.0.1+
- Ollama local por defecto
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime
import logging
import json
import re

# ✅ CORREGIDO: Imports condicionales para CrewAI 1.9.3
try:
    from crewai import Agent as CrewAIAgent, LLM as CrewLLM

    _HAS_CREWAI = True
except ImportError:
    _HAS_CREWAI = False
    CrewAIAgent = None
    CrewLLM = None

try:
    from langchain_ollama import ChatOllama, OllamaEmbeddings

    _HAS_LANGCHAIN_OLLAMA = True
except ImportError:
    _HAS_LANGCHAIN_OLLAMA = False
    ChatOllama = None
    OllamaEmbeddings = None

logger = logging.getLogger(__name__)


class AgentLevel(Enum):
    """Niveles jerárquicos de agentes"""
    STRATEGIC = 1  # Nivel 1: Director, Arquitecto, Auditor
    SPECIALIST = 2  # Nivel 2: Backend, Frontend, DB, DevOps, etc.
    EXECUTION = 3  # Nivel 3: Coder, Tester, Documenter, ToolBuilder


class AgentStatus(Enum):
    """Estados posibles del agente"""
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


class BaseAgent(ABC):
    """
    Clase base para todos los agentes de DevMind Core.

    Características:
    - Identidad y metadata del agente
    - Integración con LLM (Ollama por defecto, CrewAI 1.9.3 compatible)
    - Gestión de estado y estadísticas
    - Ejecución de tareas con contexto
    """

    DEFAULT_OLLAMA_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "llama3"

    def __init__(
            self,
            name: str,
            role: str,
            goal: str,
            backstory: str,
            level: AgentLevel,
            model: str = DEFAULT_MODEL,
            temperature: float = 0.7,
            verbose: bool = True,
            ollama_host: str = DEFAULT_OLLAMA_HOST,
            **kwargs
    ):
        """
        Inicializa un agente base.

        Args:
            name: Nombre del agente
            role: Rol/función del agente
            goal: Objetivo principal
            backstory: Contexto/personalidad
            level: Nivel jerárquico
            model: Modelo LLM a usar
            temperature: Temperatura para generación
            verbose: Logging detallado
            ollama_host: URL del servidor Ollama
            **kwargs: Parámetros adicionales
        """
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.level = level
        self.model = model
        self.temperature = temperature
        self.verbose = verbose
        self.ollama_host = ollama_host

        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_active = None
        self.tasks_completed = 0
        self.tasks_failed = 0

        # ✅ CORREGIDO: Inicializar LLM compatible con CrewAI 1.9.3
        self.llm = self._init_crewai_llm()

        # ✅ CORREGIDO: Inicializar CrewAI Agent con manejo de errores
        self.crew_agent = self._create_crew_agent()

    def _init_crewai_llm(self) -> Optional[Any]:
        """
        Inicializa LLM compatible con CrewAI 1.9.3.

        ✅ Usa crewai.LLM con configuración de Ollama
        ✅ Fallback a mock si Ollama no está disponible
        """
        if not _HAS_CREWAI:
            logger.warning("crewai no instalado, usando fallback")
            return self._create_mock_llm()

        # Verificar que Ollama esté disponible
        if not self._check_ollama_available():
            logger.warning(f"Ollama no disponible en {self.ollama_host}, usando fallback")
            return self._create_mock_llm()

        try:
            # ✅ CORREGIDO: Usar crewai.LLM (no langchain) para CrewAI 1.9.3
            return CrewLLM(
                model=f"ollama/{self.model}",
                base_url=self.ollama_host,
                temperature=self.temperature,
                timeout=60,
                max_tokens=4096
            )
        except Exception as e:
            logger.error(f"Failed to initialize CrewAI LLM: {e}")
            return self._create_mock_llm()

    def _create_mock_llm(self) -> Any:
        """Crea un mock de LLM para modo offline/desarrollo"""
        from unittest.mock import MagicMock

        mock = MagicMock()
        mock.invoke.return_value = MagicMock(
            content=f"⚠️ Modo offline: Ollama no disponible en {self.ollama_host}"
        )
        mock.stream.return_value = iter(["⚠️ ", "Modo ", "offline"])
        return mock

    def _create_crew_agent(self) -> Optional[Any]:
        """
        Crea el agente CrewAI subyacente.

        ✅ CORREGIDO para CrewAI 1.9.3: pasar crewai.LLM o mock compatible
        """
        if not _HAS_CREWAI:
            logger.warning("crewai no instalado, agente operará en modo limitado")
            return None

        try:
            # ✅ CORREGIDO: self.llm ya es crewai.LLM o mock compatible
            return CrewAIAgent(
                role=self.role,
                goal=self.goal,
                backstory=self.backstory,
                llm=self.llm,  # ✅ Ahora es crewai.LLM o mock
                verbose=self.verbose,
                allow_delegation=(self.level != AgentLevel.EXECUTION)
            )
        except Exception as e:
            logger.error(f"Failed to create CrewAI agent: {e}")
            logger.info("Continuando sin CrewAI integration - agente funcional en modo básico")
            return None

    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Ejecuta una tarea y retorna resultado.

        Args:
            task: Descripción de la tarea
            context: Contexto adicional para la ejecución

        Returns:
            Dict con resultado de la ejecución
        """
        pass

    def can_execute(self, task: str) -> bool:
        """Verifica si el agente puede ejecutar la tarea"""
        return self.status == AgentStatus.IDLE

    def get_status(self) -> Dict[str, Any]:
        """Retorna estado actual del agente"""
        return {
            'id': self.id,
            'name': self.name,
            'role': self.role,
            'level': self.level.value,
            'status': self.status.value,
            'tasks_completed': self.tasks_completed,
            'tasks_failed': self.tasks_failed,
            'last_active': self.last_active.isoformat() if self.last_active else None,
            'model': self.model,
            'ollama_available': self._check_ollama_available(),
            'crewai_available': _HAS_CREWAI
        }

    def _check_ollama_available(self) -> bool:
        """Verifica si Ollama está disponible en la URL configurada"""
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.ollama_host}/api/tags", timeout=2)
            return True
        except Exception:
            return False

    def _update_status(self, status: AgentStatus):
        """Actualiza el estado del agente"""
        self.status = status
        if status == AgentStatus.WORKING:
            self.last_active = datetime.now()

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """
        Parsea respuesta JSON del LLM de forma robusta.

        Args:
            content: Contenido crudo de la respuesta del LLM

        Returns:
            Dict con los datos parseados o contenido raw
        """
        # Intentar extraer JSON de diferentes formatos
        patterns = [
            r'\{.*\}',  # JSON simple
            r'```json\s*(.*?)\s*```',  # JSON en bloque markdown
            r'```.*?\n(.*?)\n```',  # Cualquier bloque de código
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if match.groups() else match.group())
                except json.JSONDecodeError:
                    continue

        # Fallback: intentar parsear todo el contenido
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Último recurso: retornar contenido raw
        return {"raw": content, "content": content}