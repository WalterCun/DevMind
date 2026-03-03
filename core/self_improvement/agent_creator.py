# devmind-core/core/self_improvement/agent_creator.py
"""
AgentCreator - Genera nuevos agentes especializados dinámicamente.

Este agente analiza brechas en las capacidades del equipo
y crea nuevos agentes para satisfacerlas.
"""

import logging
import json
import re
from typing import Dict, Any, Optional, List, Type
from datetime import datetime

from ..agents.base import BaseAgent, AgentLevel, AgentStatus
from ..agents.registry import AgentRegistry
from ..tools.registry import ToolRegistry
from ..config.schema import AgentConfig

logger = logging.getLogger(__name__)


class AgentCreatorAgent(BaseAgent):
    """
    Agente especializado en crear nuevos agentes.

    Características:
    - Detecta brechas en capacidades del equipo
    - Genera configuraciones de nuevos agentes
    - Crea clases de agentes dinámicamente
    - Registra nuevos agentes en el registry
    - Valida con CapabilityValidator antes de activar
    """

    def __init__(self, **kwargs):
        super().__init__(
            name="Agent Creator",
            role="Creador de Agentes Autónomo",
            goal="Crear y registrar nuevos agentes especializados para expandir las capacidades del equipo",
            backstory="""Eres un arquitecto de sistemas multi-agente experto en diseñar
            agentes especializados que complementan las capacidades existentes.
            Siempre validas que los nuevos agentes cumplan con estándares de seguridad
            y no entren en conflicto con agentes existentes.""",
            level=AgentLevel.STRATEGIC,
            **kwargs
        )

        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        self.agents_created = 0
        self.agents_validated = 0

    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Crea un nuevo agente basado en la descripción.

        Flujo:
        1. Analizar brecha de capacidad
        2. Diseñar agente
        3. Generar configuración
        4. Validar con CapabilityValidator
        5. Registrar agente

        Args:
            task: Descripción del agente a crear
            context: Contexto del proyecto/equipo actual

        Returns:
            Dict con resultado de la creación
        """
        self._update_status(AgentStatus.WORKING)
        context = context or {}

        try:
            # Paso 1: Analizar brecha de capacidad
            gap_analysis = self._analyze_capability_gap(task, context)
            logger.info(f"Análisis de brecha: {gap_analysis.get('gap', 'unknown')}")

            # Paso 2: Diseñar agente
            design = self._design_agent(gap_analysis)
            logger.info(f"Diseño de agente: {design.get('name', 'unknown')}")

            # Paso 3: Generar configuración
            config = self._generate_agent_config(design)

            # Paso 4: Validar agente
            validation = self._validate_agent(config)

            if validation.get("valid"):
                # Paso 5: Registrar agente
                registration = self._register_agent(config)

                self.agents_created += 1

                return {
                    "success": True,
                    "agent_name": design.get("name"),
                    "agent_id": registration.get("agent_id"),
                    "level": design.get("level"),
                    "validation": validation,
                    "message": f"Agente '{design.get('name')}' creado y registrado exitosamente"
                }
            else:
                return {
                    "success": False,
                    "error": "El agente no pasó validación",
                    "validation_errors": validation.get("errors", [])
                }

        except Exception as e:
            logger.error(f"AgentCreator error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            self._update_status(AgentStatus.IDLE)

    def _analyze_capability_gap(
            self,
            task: str,
            context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analiza qué capacidades faltan en el equipo actual"""
        # Obtener estado actual del equipo
        team_status = self.agent_registry.get_status_summary()

        prompt = f"""
        Analiza las brechas de capacidad en el equipo actual:

        TAREA REQUERIDA: {task}
        CONTEXTO: {json.dumps(context, indent=2)}

        EQUIPO ACTUAL:
        {json.dumps(team_status, indent=2)}

        Proporciona un análisis con:
        1. required_capability: Capacidad específica requerida para la tarea
        2. existing_agents: Lista de agentes existentes que podrían ayudar parcialmente
        3. gap: Descripción clara de qué falta exactamente
        4. agent_type: Tipo necesario (STRATEGIC=1, SPECIALIST=2, EXECUTION=3)
        5. required_skills: Lista de 5-10 habilidades específicas requeridas
        6. required_tools: Lista de herramientas que necesitaría acceso
        7. success_metrics: 3-5 métricas para medir éxito del nuevo agente
        8. risks: Posibles riesgos de crear este agente

        Responde SOLO en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _design_agent(self, gap_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Diseña la configuración del nuevo agente"""
        prompt = f"""
        Diseña un nuevo agente basado en este análisis de brechas:

        {json.dumps(gap_analysis, indent=2)}

        Proporciona:
        1. name: Nombre del agente (PascalCase, único, descriptivo)
        2. role: Rol específico en 1 frase
        3. goal: Goal principal (1 frase clara y accionable)
        4. backstory: 2-3 párrafos que definan personalidad y enfoque
        5. level: Nivel jerárquico como string: "STRATEGIC", "SPECIALIST", o "EXECUTION"
        6. model: Modelo LLM recomendado (ej: "llama3", "codellama")
        7. temperature: Temperatura recomendada (0.0-1.0)
        8. tools: Lista de nombres de herramientas que debería tener acceso
        9. permissions: Lista de permisos necesarios (ActionType values)
        10. success_metrics: Lista de métricas específicas para este agente

        Responde SOLO en formato JSON válido.
        """

        response = self.llm.invoke(prompt)
        return self._parse_json_response(response.content)

    def _generate_agent_config(self, design: Dict[str, Any]) -> Dict[str, Any]:
        """Genera configuración completa del agente"""
        # Mapear nivel de string a enum
        level_map = {
            "STRATEGIC": AgentLevel.STRATEGIC,
            "SPECIALIST": AgentLevel.SPECIALIST,
            "EXECUTION": AgentLevel.EXECUTION,
            1: AgentLevel.STRATEGIC,
            2: AgentLevel.SPECIALIST,
            3: AgentLevel.EXECUTION,
        }

        level_value = design.get("level", "EXECUTION")
        level = level_map.get(level_value, AgentLevel.EXECUTION)
        if isinstance(level_value, str) and level_value.isdigit():
            level = level_map.get(int(level_value), AgentLevel.EXECUTION)

        config = {
            "name": design.get("name", "CustomAgent"),
            "role": design.get("role", "Specialist"),
            "goal": design.get("goal", "Complete assigned tasks effectively"),
            "backstory": design.get("backstory", ""),
            "level": level,
            "model": design.get("model", "llama3"),
            "temperature": float(min(1.0, max(0.0, design.get("temperature", 0.7)))),
            "tools": design.get("tools", []),
            "permissions": design.get("permissions", []),
            "success_metrics": design.get("success_metrics", [])
        }

        return config

    def _validate_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Valida la configuración del agente"""
        errors = []

        # Validaciones básicas de campos requeridos
        required_fields = ["name", "role", "goal"]
        for field in required_fields:
            if not config.get(field):
                errors.append(f"Campo requerido faltante o vacío: {field}")

        # Verificar unicidad de nombre/rol
        try:
            existing = self.agent_registry.get_agent_by_role(config["name"])
            if existing:
                errors.append(f"Ya existe un agente con nombre/rol: {config['name']}")
        except:
            pass  # Ignorar si el registry no está disponible

        # Validar nivel - aceptar string, enum, o int
        level_value = config.get("level")
        if hasattr(level_value, 'value'):
            level_value = level_value.value
        elif hasattr(level_value, 'name'):
            level_value = level_value.name

        valid_levels = ["STRATEGIC", "SPECIALIST", "EXECUTION", 1, 2, 3]
        if level_value not in valid_levels:
            errors.append(f"Nivel de agente inválido: {config.get('level')}")

        # Validar temperatura
        temp = config.get("temperature", 0.7)
        if isinstance(temp, (int, float)) and not (0.0 <= temp <= 1.0):
            errors.append("Temperatura debe estar entre 0.0 y 1.0")

        # Validar herramientas asignadas
        if "tools" in config:
            for tool_name in config["tools"]:
                tool = self.tool_registry.get(tool_name)
                if not tool:
                    errors.append(f"Herramienta no encontrada: {tool_name}")

        # Validar permisos (básico)
        if "permissions" in config:
            from ..security.permissions import ActionType
            valid_actions = [a.value for a in ActionType]
            for perm in config["permissions"]:
                if perm not in valid_actions:
                    errors.append(f"Permiso inválido: {perm}")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "config_summary": {
                "name": config.get("name"),
                "level": config.get("level"),
                "tools_count": len(config.get("tools", [])),
                "permissions_count": len(config.get("permissions", []))
            }
        }

    def _register_agent(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Registra el agente en el registry"""
        try:
            # Crear instancia del agente usando la clase base
            agent = BaseAgent(
                name=config["name"],
                role=config["role"],
                goal=config["goal"],
                backstory=config.get("backstory", ""),
                level=config["level"],
                model=config.get("model", "llama3"),
                temperature=config.get("temperature", 0.7)
            )

            # Registrar
            agent_id = self.agent_registry.register(agent)
            self.agents_validated += 1

            return {
                "registered": True,
                "agent_id": agent_id,
                "agent_name": config["name"],
                "level": config["level"]
            }

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            return {
                "registered": False,
                "error": str(e)
            }

    def _parse_json_response(self, content: str) -> Dict[str, Any]:
        """Parsea respuesta JSON del LLM de forma robusta"""
        patterns = [
            r'\{.*\}',
            r'```json\s*(.*?)\s*```',
            r'```.*?\n(.*?)\n```',
        ]

        for pattern in patterns:
            match = re.search(pattern, content, re.DOTALL)
            if match:
                try:
                    return json.loads(match.group(1) if len(match.groups()) > 0 else match.group())
                except json.JSONDecodeError:
                    continue

        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        return {"raw": content}

    def get_stats(self) -> Dict[str, Any]:
        """Obtiene estadísticas del AgentCreator"""
        return {
            "agents_created": self.agents_created,
            "agents_validated": self.agents_validated,
            "success_rate": round(
                self.agents_validated / max(1, self.agents_created) * 100, 1
            ) if self.agents_created > 0 else 0.0,
            "current_team_size": len(self.agent_registry)
        }