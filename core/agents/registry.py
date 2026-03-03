from typing import Dict, List, Optional, Type, Any
from .base import BaseAgent, AgentLevel


class AgentRegistry:
    """Registro central de agentes disponibles"""

    _instance = None
    _agents: Dict[str, BaseAgent] = {}
    _hierarchy: Dict[int, List[str]] = {1: [], 2: [], 3: []}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def initialize(cls, config):
        """Inicializa todos los agentes según configuración"""
        registry = cls()

        # Nivel 1 - Estratégico (siempre activos)
        from .level1_strategic.director import DirectorAgent
        from .level1_strategic.architect import ArchitectAgent
        from .level1_strategic.auditor import AuditorAgent

        registry.register(DirectorAgent())
        registry.register(ArchitectAgent())
        registry.register(AuditorAgent())

        # Nivel 2 - Especialistas (según configuración)
        if config.enable_all_agents or 'backend' in config.priority_agents:
            from .level2_specialist.backend import BackendSpecialistAgent
            registry.register(BackendSpecialistAgent())

        # ... registrar otros agentes según config

        # Nivel 3 - Ejecución (siempre activos)
        from .level3_execution.coder import CoderAgent
        from .level3_execution.tester import TesterAgent
        from .level3_execution.documenter import DocumenterAgent
        from .level3_execution.tool_builder import ToolBuilderAgent

        registry.register(CoderAgent())
        registry.register(TesterAgent())
        registry.register(DocumenterAgent())
        registry.register(ToolBuilderAgent())

    def register(self, agent: BaseAgent):
        """Registra un agente"""
        self._agents[agent.id] = agent
        self._hierarchy[agent.level.value].append(agent.id)

    def get_agent(self, agent_id: str) -> Optional[BaseAgent]:
        """Obtiene un agente por ID"""
        return self._agents.get(agent_id)

    def get_agents_by_level(self, level: AgentLevel) -> List[BaseAgent]:
        """Obtiene todos los agentes de un nivel"""
        return [self._agents[id] for id in self._hierarchy[level.value]
                if id in self._agents]

    def get_agent_by_role(self, role: str) -> Optional[BaseAgent]:
        """Obtiene agente por rol"""
        for agent in self._agents.values():
            if agent.role.lower() == role.lower():
                return agent
        return None

    def get_all_agents(self) -> List[BaseAgent]:
        """Retorna todos los agentes"""
        return list(self._agents.values())

    def get_status_summary(self) -> Dict[str, Any]:
        """Retorna resumen de estado de todos los agentes"""
        return {
            'total': len(self._agents),
            'by_level': {
                'strategic': len(self._hierarchy[1]),
                'specialist': len(self._hierarchy[2]),
                'execution': len(self._hierarchy[3])
            },
            'agents': [agent.get_status() for agent in self._agents.values()]
        }