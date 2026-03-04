# devmind-core/core/orchestrator.py
"""
Orquestador central de DevMind Core.

Coordina agentes, memoria y ejecución para proporcionar
una experiencia de desarrollo autónoma coherente.
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from .agents.base import AgentLevel
from .agents.registry import AgentRegistry
from .config.manager import ConfigManager
from .memory.relational_store import RelationalMemory
from .memory.vector_store import VectorMemory, MemoryCategory
from .utils.helpers import safe_get

logger = logging.getLogger(__name__)


class DevMindOrchestrator:
    """
    Cerebro central que orquesta todos los componentes de DevMind.

    Responsabilidades:
    - Inicialización y gestión del ciclo de vida
    - Enrutamiento de intenciones a agentes apropiados
    - Coordinación de memoria dual (vectorial + relacional)
    - Gestión de contexto entre conversaciones
    - Ejecución segura de tareas con sandbox
    """

    def __init__(
            self,
            project_id: str = None,
            config: Any = None,
            chroma_url: str = None,
            ollama_url: str = None,
            db_url: str = None
    ):
        """
        Inicializa el orquestador.

        Args:
            project_id: ID del proyecto actual (se genera si None)
            config: Configuración del agente (usa ConfigManager si None)
            chroma_url: URL de ChromaDB
            ollama_url: URL de Ollama
            db_url: URL de PostgreSQL
        """
        self.project_id = project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Cargar configuración
        self.config = config or ConfigManager().get_config()

        # Inicializar componentes
        self.vector_memory = VectorMemory(
            project_id=self.project_id,
            chroma_url=chroma_url,
            ollama_url=ollama_url
        )
        self.relational_memory = RelationalMemory(db_url=db_url)
        self.agent_registry = AgentRegistry()

        # Estado del orquestador
        self._initialized = False
        self._current_session = None
        self._task_queue = asyncio.Queue()

        logger.info(f"DevMindOrchestrator initialized for project {self.project_id}")

    def initialize(self) -> bool:
        logger.info("Starting orchestrator initialization...")

        if self._initialized:
            logger.debug("Orchestrator already initialized")
            return True

        try:
            logger.info("Initializing agent registry...")
            self.agent_registry.initialize(self.config)
            logger.info(f"Agent registry initialized with {len(self.agent_registry)} agents")

            # Crear proyecto en memoria relacional
            logger.info("Checking/creating project in relational memory...")
            try:
                project = self.relational_memory.get_project(self.project_id)
                if not project:
                    logger.info(f"Creating new project: {self.project_id}")
                    project = self.relational_memory.create_project(
                        name=f"Project {self.project_id[-8:]}",
                        description="Nuevo proyecto DevMind",
                        tech_stack={"languages": self.config.preferred_languages}
                    )
                    logger.info(f"Project created with ID: {project.id}")
                else:
                    logger.info(f"Project already exists: {project.id}")
            except Exception as db_error:
                logger.error(f"Database error during project creation: {db_error}")
                logger.error("Tip: Run 'uv run python manage.py migrate --run-syncdb'")
                raise

            self._initialized = True
            logger.info("✅ DevMindOrchestrator fully initialized")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to initialize orchestrator: {type(e).__name__}: {e}", exc_info=True)
            return False

    async def process_message(
            self,
            message: str,
            session_id: str = None,
            metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Procesa un mensaje del usuario y retorna respuesta del agente.

        Flujo:
        1. Clasificar intención
        2. Recuperar contexto de memoria
        3. Seleccionar/agrupar agentes apropiados
        4. Ejecutar tarea(s)
        5. Almacenar resultados en memoria
        6. Retornar respuesta estructurada

        Args:
            message: Mensaje del usuario
            session_id: ID de sesión de conversación
            metadata: Metadata adicional

        Returns:
            Respuesta estructurada con contenido, archivos, sugerencias
        """
        if not self._initialized:
            return {"error": "Orchestrator not initialized"}

        # Obtener o crear sesión
        session = self._get_or_create_session(session_id, message)

        # Clasificar intención (simplificado - en producción usar LLM router)
        intent = self._classify_intent(message)

        # Recuperar contexto relevante de memoria
        context = self._build_context(message, intent)

        # Seleccionar agente(s) apropiado(s)
        agents = self._select_agents(intent, context)

        # Ejecutar tarea(s)
        result = await self._execute_task(agents, message, context, metadata)

        # Almacenar interacción en memoria
        self._store_interaction(message, result, intent, session)

        # Formatear respuesta para el usuario
        return self._format_response(result, intent)

    def _classify_intent(self, message: str) -> str:
        """
        Clasifica la intención del mensaje del usuario.

        En producción, esto usaría un LLM para clasificación.
        Aquí usamos reglas simples basadas en keywords.
        """
        message_lower = message.lower()

        if any(kw in message_lower for kw in ["plan", "planificar", "etapa", "fase"]):
            return "plan"
        elif any(kw in message_lower for kw in ["código", "code", "implementar", "crear"]):
            return "code"
        elif any(kw in message_lower for kw in ["bug", "error", "falla", "corregir", "fix"]):
            return "fix"
        elif any(kw in message_lower for kw in ["explicar", "qué es", "cómo funciona"]):
            return "explain"
        elif any(kw in message_lower for kw in ["stack", "tecnología", "librería", "framework"]):
            return "stack"
        elif any(kw in message_lower for kw in ["conectar", "api", "integrar", "database"]):
            return "connect"
        else:
            return "general"

    def _build_context(self, message: str, intent: str) -> Dict[str, Any]:
        """Construye contexto enriquecido desde memoria"""
        context = {
            "project_id": self.project_id,
            "intent": intent,
            "timestamp": datetime.now().isoformat()
        }

        # Recuperar conocimiento relevante de memoria vectorial
        categories = self._get_relevant_categories(intent)
        knowledge = self.vector_memory.get_project_knowledge(
            query=message,
            include_categories=categories
        )
        if knowledge:
            context["retrieved_knowledge"] = knowledge

        # Obtener estado actual del proyecto
        project = self.relational_memory.get_project(self.project_id)
        if project:
            context["project_status"] = project.status
            context["current_phase"] = project.current_phase

        # Agregar configuración del agente
        if self.config:
            context["agent_config"] = {
                "autonomy_mode": self.config.autonomy_mode,
                "preferred_languages": self.config.preferred_languages,
                "sandbox_enabled": self.config.sandbox_enabled
            }

        return context

    def _get_relevant_categories(self, intent: str) -> Optional[List[MemoryCategory]]:
        """Mapea intención a categorías de memoria relevantes"""
        mapping = {
            "code": [MemoryCategory.CODE, MemoryCategory.DECISIONS, MemoryCategory.TOOLS],
            "fix": [MemoryCategory.CODE, MemoryCategory.BUGS, MemoryCategory.CONVERSATIONS],
            "plan": [MemoryCategory.REQUIREMENTS, MemoryCategory.DECISIONS],
            "explain": [MemoryCategory.DOCUMENTATION, MemoryCategory.DECISIONS],
            "stack": [MemoryCategory.DECISIONS, MemoryCategory.DOCUMENTATION],
            "connect": [MemoryCategory.DECISIONS, MemoryCategory.DOCUMENTATION],
        }
        return mapping.get(intent)

    def _select_agents(self, intent: str, context: Dict) -> List[Any]:
        """Selecciona agentes apropiados para la intención"""
        # Mapeo simplificado de intención a rol de agente
        role_mapping = {
            "plan": "Project Director",
            "code": "Backend Specialist",  # Podría ser dinámico según stack
            "fix": "QA Specialist",
            "explain": "Architect Principal",
            "stack": "Architect Principal",
            "connect": "DevOps Specialist",
            "general": "Project Director",
        }

        role = role_mapping.get(intent, "Project Director")
        agent = self.agent_registry.get_agent_by_role(role)

        if agent:
            return [agent]

        # Fallback: usar cualquier agente disponible del nivel apropiado
        fallback_level = AgentLevel.STRATEGIC if intent in ["plan", "stack"] else AgentLevel.SPECIALIST
        available = self.agent_registry.get_agents_by_level(fallback_level)

        return available[:1] if available else []

    async def _execute_task(
            self,
            agents: List[Any],
            task: str,
            context: Dict,
            metadata: Dict = None
    ) -> Dict[str, Any]:
        """Ejecuta tarea en agente(s) seleccionados"""
        if not agents:
            return {"error": "No suitable agent found for task"}

        results = []

        for agent in agents:
            try:
                # Ejecutar de forma asíncrona si el agente lo soporta
                if hasattr(agent, 'execute_async'):
                    result = await agent.execute_async(task, context)
                else:
                    # Ejecutar en thread pool para no bloquear
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None,
                        lambda: agent.execute(task, context)
                    )

                results.append({
                    "agent": agent.name,
                    "result": result,
                    "success": True
                })

            except Exception as e:
                logger.error(f"Agent {agent.name} execution failed: {e}")
                results.append({
                    "agent": agent.name,
                    "error": str(e),
                    "success": False
                })

        # Combinar resultados si hay múltiples agentes
        if len(results) == 1:
            return results[0]

        return {
            "multi_agent": True,
            "results": results,
            "combined": self._combine_results(results)
        }

    def _combine_results(self, results: List[Dict]) -> Dict[str, Any]:
        """Combina resultados de múltiples agentes"""
        combined = {"content": [], "files": [], "suggestions": []}

        for r in results:
            if r.get("success") and "result" in r:
                result = r["result"]
                if isinstance(result, dict):
                    combined["content"].append(result.get("content", ""))
                    combined["files"].extend(result.get("files_to_create", []))
                    combined["suggestions"].extend(result.get("recommendations", []))
                else:
                    combined["content"].append(str(result))

        return {
            "content": "\n\n".join(filter(None, combined["content"])),
            "files": combined["files"],
            "suggestions": combined["suggestions"]
        }

    def _store_interaction(
            self,
            message: str,
            result: Dict,
            intent: str,
            session: Any
    ) -> None:
        """Almacena la interacción en memoria para contexto futuro"""
        # Guardar en memoria vectorial (siempre funciona)
        try:
            self.vector_memory.store_conversation(
                user_message=message,
                agent_response=str(result.get("content", result))[:2000],
                intent=intent
            )
        except Exception as e:
            logger.warning(f"Failed to store in vector memory: {e}")

        # Guardar en memoria relacional SOLO si la sesión es una instancia real de Django
        if session and hasattr(session, 'id') and hasattr(session, 'project_id'):
            try:
                # Verificar que es una instancia real de ConversationSession
                from db.models import ConversationSession
                if isinstance(session, ConversationSession):
                    self.relational_memory.add_message(
                        session=session,
                        role="user",
                        content=message,
                        intent=intent
                    )
                    self.relational_memory.add_message(
                        session=session,
                        role="agent",
                        content=str(result)[:5000],
                        metadata={"intent": intent, "result_keys": list(result.keys())}
                    )
            except Exception as e:
                logger.debug(f"Skipping relational storage (fallback session): {e}")

    def _format_response(self, result: Dict, intent: str) -> Dict[str, Any]:
        """Formatea resultado para respuesta al usuario"""
        # Extraer contenido principal con múltiples fallbacks
        content = None

        # Intentar extraer de diferentes estructuras de resultado
        if isinstance(result, dict):
            content = (
                    result.get("content") or
                    result.get("response") or
                    result.get("answer") or
                    (result.get("result") if isinstance(result.get("result"), str) else None) or
                    (result.get("result", {}).get("content") if isinstance(result.get("result"), dict) else None)
            )

        # Si content sigue siendo None, convertir el resultado completo a string
        if not content:
            content = str(result)

        # Limpiar contenido vacío
        if not content or content.strip() == "":
            content = "⚠️ No se generó una respuesta válida. Por favor, intenta de nuevo."

        return {
            "response": content.strip(),
            "intent": intent,
            "files_modified": result.get("files") or result.get("combined", {}).get("files", []) if isinstance(result,
                                                                                                               dict) else [],
            "suggestions": result.get("suggestions") or result.get("combined", {}).get("suggestions", []) if isinstance(
                result, dict) else [],
            "agent_info": {
                "name": result.get("agent"),
                "execution_time": result.get("execution_time")
            } if isinstance(result, dict) and result.get("success") else None,
            "error": result.get("error") if isinstance(result, dict) and not result.get("success") else None
        }

    def _get_or_create_session(self, session_id: str, message: str) -> Any:
        """Obtiene o crea sesión de conversación"""
        # Intentar obtener proyecto primero
        project = self.relational_memory.get_project(self.project_id)

        if not project:
            # Fallback: crear objeto simple si no hay proyecto en DB
            logger.warning(f"Project {self.project_id} not found in relational memory, using fallback session")
            return type('Session', (), {
                'id': f"session_{datetime.now().timestamp()}",
                'project_id': self.project_id
            })()

        # Si hay session_id, intentar recuperar de DB (simplificado para pruebas)
        if session_id:
            # En producción: buscar ConversationSession.objects.get(session_id=session_id)
            pass

        # Crear nueva sesión en la base de datos
        try:
            session = self.relational_memory.create_conversation_session(
                project=project,
                purpose=message[:100] if message else "Nueva conversación",
                session_id=session_id
            )
            logger.debug(f"Created conversation session: {session.id}")
            return session
        except Exception as e:
            logger.warning(f"Failed to create DB session: {e}, using fallback")
            # Fallback: objeto simple
            return type('Session', (), {
                'id': f"session_{datetime.now().timestamp()}",
                'project_id': self.project_id,
                'project': project  # Incluir proyecto para que add_message funcione
            })()

    async def shutdown(self) -> None:
        """Limpia recursos antes de cerrar"""
        logger.info("Shutting down DevMindOrchestrator...")

        # Esperar tareas pendientes
        while not self._task_queue.empty():
            await asyncio.sleep(0.1)

        # Guardar estado si es necesario
        # ...

        logger.info("DevMindOrchestrator shutdown complete")

    def get_status(self) -> Dict[str, Any]:
        """Obtiene estado actual del orquestador"""
        return {
            "project_id": self.project_id,
            "initialized": self._initialized,
            "config": {
                "agent_name": safe_get(self.config, "agent_name"),
                "autonomy_mode": safe_get(self.config, "autonomy_mode"),
            } if self.config else None,
            "memory": {
                "vector": self.vector_memory.get_stats(),
                "relational": "connected" if self.relational_memory else "disconnected"
            },
            "agents": self.agent_registry.get_status_summary()
        }

    def __repr__(self) -> str:
        return f"DevMindOrchestrator(project={self.project_id}, initialized={self._initialized})"
