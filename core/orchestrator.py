# core/orchestrator.py
"""
Orquestador central de DevMind Core.
Coordina agentes, memoria y ejecución para proporcionar
una experiencia de desarrollo autónoma coherente.
"""
import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List

from .agents import AgentLevel
from .agents.registry import AgentRegistry
from .config.manager import ConfigManager
from .memory.relational_store import RelationalMemory
from .memory.vector_store import VectorMemory, MemoryCategory
from .utils.helpers import safe_get
from pathlib import Path
import os

logger = logging.getLogger(__name__)


class DevMindOrchestrator:
    """
    Cerebro central que orquesta todos los componentes de DevMind.
    """

    def __init__(
            self,
            project_id: str = None,
            config: Any = None,
            chroma_url: str = None,
            ollama_url: str = None,
            db_url: str = None
    ):
        self.project_id = project_id or f"project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.config = config or ConfigManager().get_config()

        self.vector_memory = VectorMemory(
            project_id=self.project_id,
            chroma_url=chroma_url,
            ollama_url=ollama_url
        )
        self.relational_memory = RelationalMemory(db_url=db_url)
        self.agent_registry = AgentRegistry()

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

    # --- NUEVO MÉTODO: CONTEXTO DE PROYECTO ---
    def _build_project_context(self) -> str:
        """
        Escanea el proyecto y devuelve un resumen del estado actual.
        Esto da 'ojos' al agente.
        """
        project_root = Path(os.getenv("PROJECT_ROOT", "."))
        context_parts = ["📊 ESTADO ACTUAL DEL PROYECTO:\n"]

        # 1. Listar estructura de archivos
        files = []
        for root, dirs, filenames in os.walk(project_root):
            # Ignorar carpetas irrelevantes
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__pycache__', 'node_modules', 'venv', '.git', 'env'))]

            level = root.replace(str(project_root), '').count(os.sep)
            if level < 2:  # Limitar profundidad
                for filename in filenames:
                    rel_path = os.path.join(root, filename).replace(str(project_root), '').strip(os.sep)
                    files.append(rel_path)

        context_parts.append(f"Archivos detectados ({len(files)}):\n- " + "\n- ".join(files[:50]))

        # 2. Detectar stack tecnológico
        stack = []
        if (project_root / "requirements.txt").exists(): stack.append("Python (pip)")
        if (project_root / "pyproject.toml").exists(): stack.append("Python (poetry/uv)")
        if (project_root / "package.json").exists(): stack.append("Node.js")

        context_parts.append(f"\nStack Tecnológico Inferido: {', '.join(stack) if stack else 'Desconocido'}")

        return "\n".join(context_parts)

    # --- NUEVO MÉTODO: BUCLE AUTÓNOMO ---
    async def execute_autonomous_task(
            self,
            task: str,
            session_id: str = None,
            max_iterations: int = 10
    ) -> Dict[str, Any]:
        """
        Ejecuta una tarea permitiendo al agente usar herramientas en un bucle
        hasta completar la tarea o alcanzar el límite de iteraciones.
        """
        from core.tools.registry import ToolRegistry

        # 1. Inicialización
        if not self._initialized:
            self.initialize()

        session = self._get_or_create_session(session_id, task)
        registry = ToolRegistry()

        # Obtener agente de ejecución (Coder)
        agent = self.agent_registry.get_agent_by_role("Coder Agent")
        if not agent:
            return {"error": "Coder Agent no disponible"}

        # 2. Construir Contexto Inicial
        project_context = self._build_project_context()
        current_task = f"{project_context}\n\n--- TAREA DEL USUARIO ---\n{task}"

        # Recuperar memoria histórica
        past_solutions = self.vector_memory.retrieve(query=task, limit=2)
        memory_context = ""
        if past_solutions:
            memory_context = "\n📚 EXPERIENCIAS PASADAS SIMILARES:\n"
            for solution in past_solutions:
                memory_context += f"- {solution.get('content', '')[:200]}...\n"
            current_task = f"{memory_context}\n{current_task}"

        iteration = 0
        history = []
        logger.info(f"🤖 Iniciando tarea autónoma: {task}")

        # 3. Bucle de Ejecución
        while iteration < max_iterations:
            iteration += 1
            logger.debug(f"Iteración autónoma {iteration}/{max_iterations}")

            # A. PENSAR: Ejecutar el agente
            result = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: agent.execute(current_task, {})
            )

            agent_output = result.get("content", str(result))

            # B. PARSEAR RESPUESTA
            parsed = agent._parse_json_response(agent_output)

            history.append(parsed)
            action = parsed.get("action", "respond")

            # C. ACTUAR
            if action == "respond":
                final_response = parsed.get("response", "Tarea completada.")
                self._store_interaction(task, {"content": final_response}, "code", session)
                return {
                    "success": True,
                    "response": final_response,
                    "iterations": iteration,
                    "history": history
                }

            elif action == "tool_use":
                tool_name = parsed.get("tool_name")
                tool_args = parsed.get("tool_args", {})

                if not tool_name:
                    current_task = "Error: Intentaste usar una herramienta pero no especificaste el nombre. Corrige tu JSON."
                    continue

                logger.info(f"🔧 Usando herramienta: {tool_name} con args {tool_args}")
                tool_result = registry.execute(tool_name, **tool_args)

                # D. OBSERVAR Y REFLEXIONAR
                observation = ""
                if not tool_result.success:
                    observation = (
                        f"❌ ERROR CRÍTICO en herramienta '{tool_name}':\n"
                        f"Salida de error:\n{tool_result.error}\n\n"
                        f"INSTRUCCIONES PARA CORRECCIÓN:\n"
                        f"1. NO repitas la misma acción.\n"
                        f"2. Analiza el mensaje de error detalladamente.\n"
                        f"3. Si es un error de sintaxis, lee el archivo con 'read_file' y compara.\n"
                        f"4. Propón una solución NUEVA."
                    )
                else:
                    observation = (
                        f"✅ ÉXITO. Herramienta '{tool_name}' ejecutada.\n"
                        f"Resultado:\n{tool_result.output}\n\n"
                        f"Basado en este éxito, ¿cuál es el siguiente paso?"
                    )

                current_task = f"Observación del paso anterior:\n{observation}\n\nTarea Original: {task}"

            else:
                current_task = f"Formato de acción inválido: '{action}'. Debes usar 'tool_use' o 'respond'."

        return {
            "success": False,
            "error": "Límite de iteraciones alcanzado sin solución final.",
            "history": history
        }

    # --- MÉTODOS EXISTENTES (Mantenidos para compatibilidad) ---

    async def process_message(self, message: str, session_id: str = None, metadata: Dict[str, Any] = None,
                              output_json: bool = False) -> Dict[str, Any]:
        # Redirigir al nuevo flujo autónomo por defecto o mantener el simple si se desea
        # Por ahora, lo mantenemos simple para no romper comandos existentes como 'status'
        if not self._initialized:
            return {"error": "Orchestrator not initialized"}

        session = self._get_or_create_session(session_id, message)
        intent = self._classify_intent(message)
        context = self._build_context(message, intent)
        agents = self._select_agents(intent, context)
        result = await self._execute_task(agents, message, context, metadata)
        self._store_interaction(message, result, intent, session)
        return self._format_response(result, intent, output_json)

    @staticmethod
    def _classify_intent(message: str) -> str:
        message_lower = message.lower()
        if any(kw in message_lower for kw in ["plan", "planificar", "etapa", "fase"]):
            return "plan"
        elif any(kw in message_lower for kw in ["código", "code", "implementar", "crear", "escribir"]):
            return "code"
        elif any(kw in message_lower for kw in ["bug", "error", "falla", "corregir", "fix"]):
            return "fix"
        elif any(kw in message_lower for kw in ["explicar", "qué es", "cómo funciona"]):
            return "explain"
        else:
            return "general"

    def _build_context(self, message: str, intent: str) -> Dict[str, Any]:
        context = {"project_id": self.project_id, "intent": intent, "timestamp": datetime.now().isoformat()}
        # Simplificado para el ejemplo
        return context

    @staticmethod
    def _get_relevant_categories(intent: str) -> Optional[List[MemoryCategory]]:
        return None  # Simplificado

    def _select_agents(self, intent: str, context: Dict) -> List[Any]:
        role_mapping = {"plan": "Project Director", "code": "Coder Agent", "fix": "QA Specialist"}
        role = role_mapping.get(intent, "Project Director")
        agent = self.agent_registry.get_agent_by_role(role)
        return [agent] if agent else []

    async def _execute_task(self, agents: List[Any], task: str, context: Dict, metadata: Dict = None) -> Dict[str, Any]:
        if not agents: return {"error": "No suitable agent found"}
        # Ejecución simple (sin bucle autónomo aquí para no duplicar lógica)
        results = []
        for agent in agents:
            try:
                if hasattr(agent, 'execute_async'):
                    result = await agent.execute_async(task, context)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, lambda: agent.execute(task, context))
                results.append({"agent": agent.name, "result": result, "success": True})
            except Exception as e:
                results.append({"agent": agent.name, "error": str(e), "success": False})
        return results[0] if len(results) == 1 else {"multi_agent": True, "results": results}

    def _store_interaction(self, message: str, result: Dict, intent: str, session: Any) -> None:
        try:
            self.vector_memory.store_conversation(user_message=message, agent_response=str(result)[:2000],
                                                  intent=intent)
        except Exception as e:
            logger.warning(f"Failed to store in vector memory: {e}")

    @staticmethod
    def _format_response(result: Dict, intent: str, output_json: bool = False) -> Dict[str, Any]:
        if output_json: return {"response": result, "intent": intent, "format": "json", **result}
        content = result.get("content") or result.get("response") or str(result)
        return {"response": content, "intent": intent, "format": "natural",
                "error": result.get("error") if not result.get("success") else None}

    def _get_or_create_session(self, session_id: str, message: str) -> Any:
        # Simplificado
        return type('Session', (), {'id': session_id or "default", 'project_id': self.project_id})()

    async def shutdown(self) -> None:
        logger.info("Shutting down DevMindOrchestrator...")

    def get_status(self) -> Dict[str, Any]:
        return {"project_id": self.project_id, "initialized": self._initialized, "agents": len(self.agent_registry)}