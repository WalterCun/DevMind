from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from enum import Enum
import uuid
from datetime import datetime

from langchain_ollama import ChatOllama
from crewai import Agent as CrewAIAgent


class AgentLevel(Enum):
    STRATEGIC = 1  # Nivel 1: Director, Arquitecto, Auditor
    SPECIALIST = 2  # Nivel 2: Backend, Frontend, DB, etc.
    EXECUTION = 3  # Nivel 3: Coder, Tester, Documenter


class AgentStatus(Enum):
    IDLE = "idle"
    WORKING = "working"
    WAITING = "waiting"
    ERROR = "error"


class BaseAgent(ABC):
    """Clase base para todos los agentes"""

    def __init__(
            self,
            name: str,
            role: str,
            goal: str,
            backstory: str,
            level: AgentLevel,
            model: str = "llama3",
            temperature: float = 0.7,
            verbose: bool = True
    ):
        self.id = str(uuid.uuid4())
        self.name = name
        self.role = role
        self.goal = goal
        self.backstory = backstory
        self.level = level
        self.model = model
        self.temperature = temperature
        self.verbose = verbose

        self.status = AgentStatus.IDLE
        self.created_at = datetime.now()
        self.last_active = None
        self.tasks_completed = 0
        self.tasks_failed = 0

        # Inicializar LLM
        self.llm = ChatOllama(
            model=model,
            base_url="http://localhost:11434",
            temperature=temperature
        )

        # Inicializar CrewAI Agent
        self.crew_agent = self._create_crew_agent()

    def _create_crew_agent(self) -> CrewAIAgent:
        """Crea el agente CrewAI subyacente"""
        return CrewAIAgent(
            role=self.role,
            goal=self.goal,
            backstory=self.backstory,
            llm=self.llm,
            verbose=self.verbose,
            allow_delegation=self.level != AgentLevel.EXECUTION
        )

    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Ejecuta una tarea y retorna resultado"""
        pass

    def can_execute(self, task: str) -> bool:
        """Verifica si el agente puede ejecutar la tarea"""
        # Implementar lógica de validación
        return True

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
            'last_active': self.last_active.isoformat() if self.last_active else None
        }

    def _update_status(self, status: AgentStatus):
        """Actualiza el estado del agente"""
        self.status = status
        if status == AgentStatus.WORKING:
            self.last_active = datetime.now()