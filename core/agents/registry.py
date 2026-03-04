# devmind-core/core/agents/registry.py
"""
Registro y gestión de agentes para DevMind Core.
Proporciona un sistema centralizado para registrar,
buscar y orquestar agentes especializados.
"""
from typing import Dict, List, Optional, Type, Any
from enum import Enum
import logging
import os
from datetime import datetime
from .base import BaseAgent, AgentLevel, AgentStatus

logger = logging.getLogger(__name__)

# ✅ Obtener modelo de LLM desde variable de entorno
DEFAULT_LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")


class AgentRegistry:
    """
    Registro centralizado de agentes con soporte jerárquico.
    """

    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, BaseAgent]
    _by_role: Dict[str, str]
    _by_level: Dict[AgentLevel, List[str]]

    def __new__(cls) -> 'AgentRegistry':
        """Implementa patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._by_role = {}
            cls._instance._by_level = {level: [] for level in AgentLevel}
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, config: Any) -> None:
        """Inicializa todos los agentes según configuración"""
        if self._initialized:
            logger.debug("AgentRegistry already initialized")
            return

        logger.info("Initializing AgentRegistry...")

        # ===========================================
        # NIVEL 1: ESTRATÉGICO (siempre activos)
        # ===========================================
        self._register_strategic_agents(config)

        # ===========================================
        # NIVEL 2: ESPECIALISTAS (según configuración)
        # ===========================================
        if config.enable_all_agents:
            self._register_all_specialists(config)
        else:
            self._register_priority_specialists(config.priority_agents, config)

        # ===========================================
        # NIVEL 3: EJECUCIÓN (siempre activos)
        # ===========================================
        self._register_execution_agents(config)

        self._initialized = True
        logger.info(f"AgentRegistry initialized with {len(self._agents)} agents")

    def _register_strategic_agents(self, config: Any) -> None:
        """Registra agentes de nivel estratégico"""
        from .level1_strategic.director import DirectorAgent
        from .level1_strategic.architect import ArchitectAgent
        from .level1_strategic.auditor import AuditorAgent

        # ✅ USAR VARIABLE DE ENTORNO para modelo
        llm_model = os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL)

        agents = [
            DirectorAgent(model=llm_model, temperature=0.3),
            ArchitectAgent(model=llm_model, temperature=0.4),
            AuditorAgent(model=llm_model, temperature=0.2)
        ]

        for agent in agents:
            self.register(agent)

    def _register_all_specialists(self, config: Any) -> None:
        """Registra todos los agentes especialistas"""
        from .level2_specialist.backend import BackendSpecialistAgent
        from .level2_specialist.frontend import FrontendSpecialistAgent
        from .level2_specialist.database import DatabaseSpecialistAgent
        from .level2_specialist.devops import DevOpsSpecialistAgent
        from .level2_specialist.security import SecuritySpecialistAgent
        from .level2_specialist.qa import QASpecialistAgent

        llm_model = os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL)

        agents = [
            BackendSpecialistAgent(model=llm_model),
            FrontendSpecialistAgent(model=llm_model),
            DatabaseSpecialistAgent(model=llm_model),
            DevOpsSpecialistAgent(model=llm_model),
            SecuritySpecialistAgent(model=llm_model),
            QASpecialistAgent(model=llm_model),
        ]

        for agent in agents:
            self.register(agent)

    def _register_priority_specialists(
            self,
            priority_agents: List[str],
            config: Any
    ) -> None:
        """Registra solo agentes especialistas prioritarios"""
        specialist_map = {
            "backend": ("level2_specialist.backend", "BackendSpecialistAgent"),
            "frontend": ("level2_specialist.frontend", "FrontendSpecialistAgent"),
            "database": ("level2_specialist.database", "DatabaseSpecialistAgent"),
            "devops": ("level2_specialist.devops", "DevOpsSpecialistAgent"),
            "security": ("level2_specialist.security", "SecuritySpecialistAgent"),
            "qa": ("level2_specialist.qa", "QASpecialistAgent"),
        }

        # ✅ USAR VARIABLE DE ENTORNO para modelo
        llm_model = os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL)

        for priority in priority_agents:
            if priority in specialist_map:
                module_path, class_name = specialist_map[priority]
                try:
                    import importlib
                    module = importlib.import_module(f"core.agents.{module_path}")
                    agent_class = getattr(module, class_name)
                    agent = agent_class(model=llm_model)  # ← Usar variable de entorno
                    self.register(agent)
                    logger.debug(f"Registered priority specialist: {priority}")
                except (ImportError, AttributeError) as e:
                    logger.warning(f"Failed to register {priority}: {e}")

    def _register_execution_agents(self, config: Any) -> None:
        """Registra agentes de nivel de ejecución"""
        from .level3_execution.coder import CoderAgent
        from .level3_execution.tester import TesterAgent
        from .level3_execution.documenter import DocumenterAgent
        from .level3_execution.tool_builder import ToolBuilderAgent

        llm_model = os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL)

        agents = [
            CoderAgent(model=llm_model),
            TesterAgent(model=llm_model),
            DocumenterAgent(model=llm_model),
            ToolBuilderAgent(model=llm_model),
        ]

        for agent in agents:
            self.register(agent)

    # ... [resto de los métodos register, unregister, get_agent, etc. se mantienen igual] ...

    def register(self, agent: BaseAgent) -> str:
        """Registra un agente en el sistema"""
        if agent.id in self._agents:
            logger.warning(f"Agent {agent.id} already registered")
            return agent.id

        self._agents[agent.id] = agent
        self._by_role[agent.role.lower()] = agent.id
        self._by_level[agent.level].append(agent.id)

        logger.debug(f"Registered agent: {agent.name} ({agent.role})")
        return agent.id

    def unregister(self, agent_id: str) -> bool:
        """Elimina un agente del registro"""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        self._by_role.pop(agent.role.lower(), None)
        if agent_id in self._by_level[agent.level]:
            self._by_level[agent.level].remove(agent_id)

        del self._agents[agent_id]
        logger.debug(f"Unregistered agent: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Obtiene agente por ID"""
        return self._agents.get(agent_id)

    def get_agent_by_role(self, role: str) -> Optional[BaseAgent]:
        """Obtiene agente por nombre de rol (case-insensitive)"""
        agent_id = self._by_role.get(role.lower())
        return self._agents.get(agent_id) if agent_id else None

    def get_agents_by_level(self, level: AgentLevel) -> List[BaseAgent]:
        """Obtiene todos los agentes de un nivel jerárquico"""
        return [
            self._agents[agent_id]
            for agent_id in self._by_level.get(level, [])
            if agent_id in self._agents
        ]

    def get_agents_by_status(self, status: AgentStatus) -> List[BaseAgent]:
        """Obtiene agentes por estado actual"""
        return [
            agent for agent in self._agents.values()
            if agent.status == status
        ]

    def get_available_agents(self) -> List[BaseAgent]:
        """Obtiene agentes disponibles (no trabajando)"""
        return [
            agent for agent in self._agents.values()
            if agent.status in [AgentStatus.IDLE, AgentStatus.WAITING]
        ]

    def assign_task(
            self,
            role: str,
            task: str,
            context: Dict[str, Any] = None
    ) -> Optional[Dict[str, Any]]:
        """Asigna y ejecuta una tarea en el agente con rol específico"""
        agent = self.get_agent_by_role(role)
        if not agent:
            logger.warning(f"No agent found for role: {role}")
            return None

        if agent.status == AgentStatus.WORKING:
            logger.debug(f"Agent {agent.name} is busy, waiting...")

        try:
            result = agent.execute(task, context)
            logger.info(f"Task executed by {agent.name}: {task[:50]}...")
            return result
        except Exception as e:
            logger.error(f"Task execution failed for {agent.name}: {e}")
            return {"error": str(e), "agent": agent.name}

    def get_status_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de estado de todos los agentes"""
        return {
            "total": len(self._agents),
            "by_level": {
                level.name: len(agent_ids)
                for level, agent_ids in self._by_level.items()
            },
            "by_status": {
                status.name: len([
                    a for a in self._agents.values() if a.status == status
                ])
                for status in AgentStatus
            },
            "agents": [
                agent.get_status() for agent in self._agents.values()
            ],
            "initialized": self._initialized
        }

    def register_custom_agent(
            self,
            agent_class: Type[BaseAgent],
            **init_kwargs
    ) -> str:
        """Registra un agente personalizado definido por el usuario"""
        try:
            agent = agent_class(**init_kwargs)
            return self.register(agent)
        except Exception as e:
            logger.error(f"Failed to register custom agent: {e}")
            raise

    def health_check(self) -> Dict[str, Any]:
        """Verifica salud de todos los agentes registrados"""
        results = {}
        for agent_id, agent in self._agents.items():
            try:
                status = agent.get_status()
                results[agent_id] = {
                    "healthy": True,
                    "status": status["status"],
                    "last_active": status.get("last_active")
                }
            except Exception as e:
                results[agent_id] = {
                    "healthy": False,
                    "error": str(e)
                }

        return {
            "timestamp": datetime.now().isoformat(),
            "total_agents": len(self._agents),
            "healthy_count": sum(1 for r in results.values() if r["healthy"]),
            "details": results
        }

    def reset(self) -> None:
        """Resetea el registro (útil para testing)"""
        self._agents.clear()
        self._by_role.clear()
        self._by_level = {level: [] for level in AgentLevel}
        self._initialized = False
        logger.info("AgentRegistry reset")

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentRegistry(agents={len(self._agents)}, initialized={self._initialized})"