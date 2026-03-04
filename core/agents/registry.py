# devmind-core/core/agents/registry.py
"""
Registro y gestión de agentes para DevMind Core.
Soporta carga dinámica (lazy loading) para optimizar inicialización.
"""

import logging
import os
from typing import Dict, List, Optional, Any, Set

from .base import BaseAgent, AgentLevel, AgentStatus

logger = logging.getLogger(__name__)

# ✅ Obtener modelo de LLM desde variable de entorno
DEFAULT_LLM_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

# ✅ Mapeo de intenciones a agentes requeridos
INTENT_AGENT_MAP = {
    "plan": ["Project Director"],
    "code": ["Backend Specialist", "Frontend Specialist"],
    "fix": ["QA Specialist", "Coder Agent"],
    "explain": ["Architect Principal"],
    "stack": ["Architect Principal", "DevOps Specialist"],
    "connect": ["DevOps Specialist"],
    "test": ["Tester Agent", "QA Specialist"],
    "document": ["Documenter Agent"],
    "tool": ["Tool Builder"],
    "general": ["Project Director"],
}

# ✅ Mapeo de roles a módulos (para carga dinámica)
AGENT_MODULE_MAP = {
    # Nivel 1 - Estratégico
    "Project Director": ("level1_strategic.director", "DirectorAgent"),
    "Architect Principal": ("level1_strategic.architect", "ArchitectAgent"),
    "Security Auditor": ("level1_strategic.auditor", "AuditorAgent"),

    # Nivel 2 - Especialistas
    "Backend Specialist": ("level2_specialist.backend", "BackendSpecialistAgent"),
    "Frontend Specialist": ("level2_specialist.frontend", "FrontendSpecialistAgent"),
    "Database Specialist": ("level2_specialist.database", "DatabaseSpecialistAgent"),
    "DevOps Specialist": ("level2_specialist.devops", "DevOpsSpecialistAgent"),
    "Security Specialist": ("level2_specialist.security", "SecuritySpecialistAgent"),
    "QA Specialist": ("level2_specialist.qa", "QASpecialistAgent"),

    # Nivel 3 - Ejecución
    "Coder Agent": ("level3_execution.coder", "CoderAgent"),
    "Tester Agent": ("level3_execution.tester", "TesterAgent"),
    "Documenter Agent": ("level3_execution.documenter", "DocumenterAgent"),
    "Tool Builder": ("level3_execution.tool_builder", "ToolBuilderAgent"),
}


class AgentRegistry:
    """
    Registro centralizado de agentes con soporte jerárquico y carga dinámica.

    Características:
    - Singleton para acceso global consistente
    - Carga dinámica (lazy loading) de agentes
    - Registro por ID, rol y nivel
    - Inicialización mínima al inicio
    - Carga bajo demanda según tarea
    - Estado y métricas por agente
    """

    _instance: Optional['AgentRegistry'] = None
    _agents: Dict[str, BaseAgent]
    _by_role: Dict[str, str]
    _by_level: Dict[AgentLevel, List[str]]
    _loaded_agents: Set[str]  # ✅ Track de agentes cargados
    _initialized: bool

    def __new__(cls) -> 'AgentRegistry':
        """Implementa patrón Singleton"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._agents = {}
            cls._instance._by_role = {}
            cls._instance._by_level = {level: [] for level in AgentLevel}
            cls._instance._loaded_agents = set()
            cls._instance._initialized = False
        return cls._instance

    def initialize(self, config: Any, minimal: bool = True) -> None:
        """
        Inicializa el registro de agentes.

        Args:
            config: Configuración del agente
            minimal: Si True, solo carga agentes core (recomendado)
                    Si False, carga todos los agentes (legacy)
        """
        if self._initialized:
            logger.debug("AgentRegistry already initialized")
            return

        logger.info("Initializing AgentRegistry...")

        # ✅ CARGA MÍNIMA por defecto (solo agentes core)
        if minimal:
            logger.info("Loading minimal agent set (core agents only)...")
            self._load_core_agents(config)
        else:
            # ✅ CARGA COMPLETA (legacy, para compatibilidad)
            if config.enable_all_agents:
                self._register_all_specialists(config)
            else:
                self._register_priority_specialists(config.priority_agents, config)

        self._initialized = True
        logger.info(f"AgentRegistry initialized with {len(self._agents)} agents loaded")

    def _load_core_agents(self, config: Any) -> None:
        """Carga solo agentes core esenciales"""
        # ✅ Solo Project Director al inicio
        core_agents = ["Project Director"]

        for role in core_agents:
            try:
                agent = self._load_agent(role, config)
                if agent:
                    self.register(agent)
            except Exception as e:
                logger.warning(f"Failed to load core agent {role}: {e}")

    def _load_agent(self, role: str, config: Any) -> Optional[BaseAgent]:
        """
        Carga un agente específico bajo demanda.

        Args:
            role: Rol del agente a cargar
            config: Configuración para inicialización

        Returns:
            Instancia del agente o None si falla
        """
        if role not in AGENT_MODULE_MAP:
            logger.error(f"Unknown agent role: {role}")
            return None

        module_path, class_name = AGENT_MODULE_MAP[role]

        try:
            import importlib
            module = importlib.import_module(f"core.agents.{module_path}")
            agent_class = getattr(module, class_name)

            # ✅ Usar modelo desde variable de entorno
            llm_model = os.getenv("OLLAMA_MODEL", DEFAULT_LLM_MODEL)

            agent = agent_class(model=llm_model)
            logger.debug(f"✅ Loaded agent: {role}")
            return agent

        except (ImportError, AttributeError) as e:
            logger.error(f"Failed to load agent {role}: {e}")
            return None

    def ensure_agents_loaded(self, intent: str, config: Any) -> List[str]:
        required_roles = INTENT_AGENT_MAP.get(intent, ["Project Director"])
        loaded = []

        for role in required_roles:
            if role not in self._loaded_agents:
                logger.info(f"🔄 Loading agent on-demand: {role} for intent '{intent}'")  # ← LOG INFO
                agent = self._load_agent(role, config)
                if agent:
                    self.register(agent)  # ← Esto ya loguea el registro
                    loaded.append(role)
            else:
                loaded.append(role)

        if loaded and os.getenv("DEVMIND_PRODUCTION", "False").lower() != "true":
            logger.info(f"✅ Loaded {len(loaded)} agents for intent '{intent}': {loaded}")

        return loaded

    def get_agents_for_intent(self, intent: str, config: Any) -> List[BaseAgent]:
        """
        Obtiene agentes apropiados para una intención, cargándolos si es necesario.

        Args:
            intent: Intención de la tarea
            config: Configuración del agente

        Returns:
            Lista de agentes listos para ejecutar
        """
        # ✅ Asegurar que los agentes estén cargados
        self.ensure_agents_loaded(intent, config)

        # Obtener agentes cargados para esta intención
        required_roles = INTENT_AGENT_MAP.get(intent, ["Project Director"])
        agents = []

        for role in required_roles:
            agent = self.get_agent_by_role(role)
            if agent:
                agents.append(agent)

        return agents

    def register(self, agent: BaseAgent) -> str:
        if agent.id in self._agents:
            logger.warning(f"Agent {agent.id} already registered")
            return agent.id

        self._agents[agent.id] = agent
        self._by_role[agent.role.strip().lower()] = agent.id
        self._by_level[agent.level].append(agent.id)
        self._loaded_agents.add(agent.role.strip())

        # ✅ LOG INFO para visibilidad en desarrollo
        if os.getenv("DEVMIND_PRODUCTION", "False").lower() != "true":
            logger.info(f"✅ Agent registered: {agent.name} ({agent.role}) - Level {agent.level.name}")
        else:
            logger.debug(f"Registered agent: {agent.name} ({agent.role})")

        return agent.id

    def _register_strategic_agents(self, config: Any) -> None:
        """Registra agentes de nivel estratégico"""
        from .level1_strategic.director import DirectorAgent
        from .level1_strategic.architect import ArchitectAgent
        from .level1_strategic.auditor import AuditorAgent

        # ✅ CORREGIDO: Usar variable de entorno para modelo de LLM
        llm_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

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

        # ✅ CORREGIDO: Usar variable de entorno para modelo de LLM
        llm_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

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

        # ✅ CORREGIDO: Usar variable de entorno para modelo de LLM
        llm_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        for priority in priority_agents:
            if priority in specialist_map:
                module_path, class_name = specialist_map[priority]
                try:
                    import importlib
                    module = importlib.import_module(f"core.agents.{module_path}")
                    agent_class = getattr(module, class_name)
                    agent = agent_class(model=llm_model)  # ← Usar llm_model correcto
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

        # ✅ CORREGIDO: Usar variable de entorno para modelo de LLM
        llm_model = os.getenv("OLLAMA_MODEL", "llama3.2:3b")

        agents = [
            CoderAgent(model=llm_model),
            TesterAgent(model=llm_model),
            DocumenterAgent(model=llm_model),
            ToolBuilderAgent(model=llm_model),
        ]

        for agent in agents:
            self.register(agent)

    def unregister(self, agent_id: str) -> bool:
        """Elimina un agente del registro"""
        if agent_id not in self._agents:
            return False

        agent = self._agents[agent_id]
        self._by_role.pop(agent.role.lower(), None)
        if agent_id in self._by_level[agent.level]:
            self._by_level[agent.level].remove(agent_id)
        self._loaded_agents.discard(agent.role)

        del self._agents[agent_id]
        logger.debug(f"Unregistered agent: {agent_id}")
        return True

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Obtiene agente por ID"""
        return self._agents.get(agent_id)

    def get_agent_by_role(self, role: str) -> Optional[BaseAgent]:
        """Obtiene agente por nombre de rol (case-insensitive)"""
        agent_id = self._by_role.get(role.strip().lower())
        return self._agents.get(agent_id) if agent_id else None

    def get_agents_by_level(self, level: AgentLevel) -> List[BaseAgent]:
        """Obtiene todos los agentes de un nivel jerárquico"""
        return [
            self._agents[agent_id]
            for agent_id in self._by_level.get(level, [])
            if agent_id in self._agents
        ]

    def get_loaded_agents_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de agentes cargados"""
        return {
            "total_loaded": len(self._loaded_agents),
            "total_registered": len(self._agents),
            "loaded_roles": list(self._loaded_agents),
            "by_level": {
                level.name: len([
                    aid for aid in agent_ids if aid in self._agents
                ])
                for level, agent_ids in self._by_level.items()
            }
        }

    # ... [resto de métodos existentes se mantienen] ...

    def get_status_summary(self) -> Dict[str, Any]:
        """Obtiene resumen de estado de todos los agentes"""
        return {
            "total": len(self._agents),
            "loaded": len(self._loaded_agents),
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

    def reset(self) -> None:
        """Resetea el registro (útil para testing)"""
        self._agents.clear()
        self._by_role.clear()
        self._by_level = {level: [] for level in AgentLevel}
        self._loaded_agents.clear()
        self._initialized = False
        logger.info("AgentRegistry reset")

    def __len__(self) -> int:
        return len(self._agents)

    def __repr__(self) -> str:
        return f"AgentRegistry(loaded={len(self._loaded_agents)}/{len(AGENT_MODULE_MAP)}, initialized={self._initialized})"
