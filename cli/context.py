# devmind-core/cli/context.py
"""
Gestión de contexto de sesión para la CLI de DevMind.

Mantiene el estado entre mensajes de chat, incluyendo:
- ID de sesión actual
- Proyecto activo
- Historial reciente de conversación
- Configuración de modo (chat, plan, code, fix)
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import uuid


class SessionContext:
    """
    Contexto de sesión para interacciones con el agente.

    Persiste entre ejecuciones de CLI para mantener continuidad.
    """

    CONTEXT_DIR = Path.home() / ".devmind" / "sessions"

    def __init__(
            self,
            session_id: str = None,
            project_id: str = None,
            mode: str = "chat"
    ):
        self.session_id = session_id or str(uuid.uuid4())
        self.project_id = project_id
        self.mode = mode  # chat, plan, code, fix, connect
        self.message_history: List[Dict[str, Any]] = []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.metadata: Dict[str, Any] = {}

    def add_message(
            self,
            role: str,
            content: str,
            intent: str = None,
            metadata: Dict[str, Any] = None
    ) -> None:
        """Agrega un mensaje al historial de la sesión"""
        self.message_history.append({
            "role": role,
            "content": content,
            "intent": intent,
            "metadata": metadata or {},
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()

    def get_recent_messages(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene los últimos N mensajes del historial"""
        return self.message_history[-limit:]

    def get_context_summary(self) -> str:
        """Genera resumen del contexto para incluir en prompts"""
        if not self.message_history:
            return ""

        recent = self.get_recent_messages(limit=5)
        summary_parts = []

        for msg in recent:
            role_label = "Usuario" if msg["role"] == "user" else "Agente"
            summary_parts.append(f"{role_label}: {msg['content'][:200]}...")

        return "\n".join(summary_parts)

    def set_project(self, project_id: str) -> None:
        """Establece el proyecto activo"""
        self.project_id = project_id
        self.metadata["project_switched_at"] = datetime.now().isoformat()

    def set_mode(self, mode: str) -> None:
        """Cambia el modo de la sesión"""
        valid_modes = ["chat", "plan", "code", "fix", "connect"]
        if mode not in valid_modes:
            raise ValueError(f"Modo inválido. Opciones: {valid_modes}")
        self.mode = mode

    def to_dict(self) -> Dict[str, Any]:
        """Serializa el contexto a diccionario"""
        return {
            "session_id": self.session_id,
            "project_id": self.project_id,
            "mode": self.mode,
            "message_history": self.message_history,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionContext":
        """Crea contexto desde diccionario"""
        ctx = cls(
            session_id=data.get("session_id"),
            project_id=data.get("project_id"),
            mode=data.get("mode", "chat")
        )
        ctx.message_history = data.get("message_history", [])
        ctx.created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.now()
        ctx.updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.now()
        ctx.metadata = data.get("metadata", {})
        return ctx

    def save(self) -> Path:
        """Guarda el contexto en archivo"""
        self.CONTEXT_DIR.mkdir(parents=True, exist_ok=True)
        file_path = self.CONTEXT_DIR / f"{self.session_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)

        return file_path

    @classmethod
    def load(cls, session_id: str) -> Optional["SessionContext"]:
        """Carga contexto desde archivo"""
        file_path = cls.CONTEXT_DIR / f"{session_id}.json"

        if not file_path.exists():
            return None

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return cls.from_dict(data)

    @classmethod
    def get_active_session(cls) -> Optional["SessionContext"]:
        """Obtiene la sesión activa más reciente"""
        if not cls.CONTEXT_DIR.exists():
            return None

        # Encontrar el archivo más reciente
        session_files = list(cls.CONTEXT_DIR.glob("*.json"))
        if not session_files:
            return None

        latest_file = max(session_files, key=lambda f: f.stat().st_mtime)
        return cls.load(latest_file.stem)

    def clear_history(self) -> None:
        """Limpia el historial de mensajes pero mantiene la sesión"""
        self.message_history = []
        self.metadata["history_cleared_at"] = datetime.now().isoformat()

    def delete(self) -> bool:
        """Elimina el archivo de sesión"""
        file_path = self.CONTEXT_DIR / f"{self.session_id}.json"
        if file_path.exists():
            file_path.unlink()
            return True
        return False


class ContextManager:
    """
    Gestor de contextos de sesión.

    Proporciona métodos convenientes para crear, cargar y cambiar entre sesiones.
    """

    def __init__(self):
        self.current_context: Optional[SessionContext] = None

    def create_session(
            self,
            project_id: str = None,
            mode: str = "chat"
    ) -> SessionContext:
        """Crea una nueva sesión"""
        self.current_context = SessionContext(
            project_id=project_id,
            mode=mode
        )
        self.current_context.save()
        return self.current_context

    def load_session(self, session_id: str) -> Optional[SessionContext]:
        """Carga una sesión existente"""
        self.current_context = SessionContext.load(session_id)
        return self.current_context

    def get_or_create_session(self, project_id: str = None, mode: str = "chat") -> SessionContext:
        """Obtiene sesión activa o crea una nueva"""
        if self.current_context:
            return self.current_context

        # Intentar cargar sesión más reciente
        recent = SessionContext.get_active_session()
        if recent:
            self.current_context = recent
            return recent

        # Crear nueva sesión
        return self.create_session(project_id=project_id, mode=mode)

    def switch_project(self, project_id: str) -> None:
        """Cambia el proyecto de la sesión actual"""
        if not self.current_context:
            self.create_session(project_id=project_id)
        else:
            self.current_context.set_project(project_id)
            self.current_context.save()

    def switch_mode(self, mode: str) -> None:
        """Cambia el modo de la sesión actual"""
        if not self.current_context:
            self.create_session(mode=mode)
        else:
            self.current_context.set_mode(mode)
            self.current_context.save()

    def add_message(
            self,
            role: str,
            content: str,
            intent: str = None,
            metadata: Dict[str, Any] = None
    ) -> None:
        """Agrega mensaje a la sesión actual"""
        if not self.current_context:
            self.create_session()

        self.current_context.add_message(role, content, intent, metadata)
        self.current_context.save()

    def get_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Obtiene historial de la sesión actual"""
        if not self.current_context:
            return []
        return self.current_context.get_recent_messages(limit)

    def clear(self) -> None:
        """Limpia la sesión actual"""
        if self.current_context:
            self.current_context.clear_history()
            self.current_context.save()

    def get_context(self) -> Optional[SessionContext]:
        """Obtiene el contexto actual"""
        return self.current_context