# devmind-core/core/agents/base.py
"""Base agent compatible with CrewAI 1.9.3+"""
import json
import logging
import os
import re
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Dict, Any, Optional

from core.agents.llm_wrapper import CrewLLMWrapper

# ✅ CrewAI 1.9.3 compatible imports
try:
    from crewai import Agent as CrewAIAgent, LLM as CrewLLM

    _HAS_CREWAI = True
except ImportError:
    _HAS_CREWAI = False
    CrewAIAgent = CrewLLM = None

logger = logging.getLogger(__name__)


class AgentLevel(Enum):
    STRATEGIC = 1
    SPECIALIST = 2
    EXECUTION = 3


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


class BaseAgent(ABC):
    DEFAULT_OLLAMA_HOST = "http://localhost:11434"
    DEFAULT_MODEL = "qwen3-coder:480b-cloud"

    def __init__(self, name: str, role: str, goal: str, backstory: str,
                 level: AgentLevel, model: str = DEFAULT_MODEL,
                 temperature: float = 0.7, verbose: bool = True,
                 ollama_host: str = DEFAULT_OLLAMA_HOST, **kwargs):
        self.id = str(uuid.uuid4())
        self.name, self.role, self.goal, self.backstory = name, role, goal, backstory
        self.level, self.temperature = level, temperature
        self.verbose = verbose
        self.model = model or os.getenv("OLLAMA_MODEL", "qwen3-coder:30b")
        self.ollama_host = ollama_host or os.getenv("OLLAMA_URL", "http://localhost:11434")
        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_active = None
        self.tasks_completed = self.tasks_failed = 0
        self.llm = self._init_crewai_llm()
        self.crew_agent = self._create_crew_agent()

    def _init_crewai_llm(self) -> Optional[Any]:
        """Inicializa LLM compatible con CrewAI 1.9.3 + interfaz LangChain"""
        logger.debug(f"Initializing LLM: model={self.model}, host={self.ollama_host}")

        if not _HAS_CREWAI:
            logger.warning("crewai not installed, using mock LLM")
            return self._create_mock_llm()

        if not self._check_ollama_available():
            logger.warning(f"Ollama not available at {self.ollama_host}, using mock LLM")
            return self._create_mock_llm()

        try:
            logger.debug(f"Creating CrewLLM with model: {self.model}, provider: ollama")

            llm = CrewLLM(
                model=self.model,
                base_url=self.ollama_host,
                api_base=self.ollama_host,
                provider="ollama",
                temperature=self.temperature,
                timeout=60,
                max_tokens=4096
            )

            logger.debug("✅ CrewLLM initialized")  # ← Cambiar a DEBUG
            return CrewLLMWrapper(llm)

        except Exception as e:
            logger.debug(f"Fallback to mock LLM: {e}")
            return self._create_mock_llm()

    @staticmethod
    def _create_mock_llm() -> Any:
        from unittest.mock import MagicMock
        mock = MagicMock()
        mock.invoke.return_value = MagicMock(content="⚠️ Offline mode")
        mock.stream.return_value = iter(["⚠️ ", "offline"])
        return mock

    def _create_crew_agent(self) -> Optional[Any]:
        if not _HAS_CREWAI:
            return None
        try:
            return CrewAIAgent(
                role=self.role, goal=self.goal, backstory=self.backstory,
                llm=self.llm, verbose=self.verbose,
                allow_delegation=(self.level != AgentLevel.EXECUTION)
            )
        except:
            return None

    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        pass

    def can_execute(self, task: str) -> bool:
        return self.status == AgentStatus.IDLE

    def get_status(self) -> Dict[str, Any]:
        return {'id': self.id, 'name': self.name, 'role': self.role,
                'level': self.level.value, 'status': self.status.value,
                'tasks_completed': self.tasks_completed,
                'tasks_failed': self.tasks_failed,
                'last_active': self.last_active.isoformat() if self.last_active else None}

    def _check_ollama_available(self) -> bool:
        try:
            import urllib.request
            urllib.request.urlopen(f"{self.ollama_host}/api/tags", timeout=2)
            return True
        except:
            return False

    def _update_status(self, status: AgentStatus):
        self.status = status
        if status == AgentStatus.WORKING:
            self.last_active = datetime.now()

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        patterns = [r'\{.*\}', r'```json\s*(.*?)\s*```', r'```.*?\n(.*?)\n```']
        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if match.groups() else match.group())
                except:
                    continue
        try:
            return json.loads(content)
        except:
            pass
        return {"raw": content, "content": content}
