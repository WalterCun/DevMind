# devmind-core/core/memory/relational_store.py
"""
Memoria relacional para DevMind Core.
Compatible con PostgreSQL y SQLite.
"""

import logging
import os
import uuid
from contextlib import contextmanager
from enum import Enum
from typing import List, Dict, Any, Optional

# ✅ FORZAR SQLite si está configurado
USE_SQLITE = os.getenv("DEVMENT_TEST_USE_SQLITE") == "True"
if USE_SQLITE:
    os.environ.setdefault("DATABASE_URL", "sqlite:///devmind_test.db")
    logging.info(f"🔧 Using SQLite: {os.getenv('DATABASE_URL')}")

# Configurar Django ANTES de importar modelos
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db.settings")

import django

django.setup()

from django.db import transaction, IntegrityError
from db.models import (
    Project, Task, ConversationSession, Message
)

logger = logging.getLogger(__name__)


class MemoryOperation(str, Enum):
    """Operaciones disponibles en memoria relacional"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    COUNT = "count"
    SEARCH = "search"


class RelationalMemory:
    """
    Memoria relacional basada en Django ORM para estado estructurado.
    Compatible con PostgreSQL y SQLite.
    """

    def __init__(self, db_url: str = None):
        """Inicializa la memoria relacional"""
        # ✅ Usar SQLite si está configurado
        if USE_SQLITE:
            self.db_url = "sqlite:///devmind_test.db"
        else:
            self.db_url = db_url or os.getenv("DATABASE_URL")

        logger.info(f"RelationalMemory initialized with: {'SQLite' if USE_SQLITE else 'PostgreSQL'}")

    @contextmanager
    def transaction(self):
        """Context manager para transacciones atómicas"""
        with transaction.atomic():
            yield

    # ===========================================
    # PROYECTOS
    # ===========================================

    def create_project(
            self,
            name: str,
            description: str,
            tech_stack: Dict[str, Any] = None,
            **kwargs
    ) -> Project:
        """Crea un nuevo proyecto"""
        try:
            project = Project.objects.create(
                name=name,
                description=description,
                tech_stack=tech_stack or {},
                **kwargs
            )
            logger.info(f"✅ Created project: {project.id} - {name}")
            return project
        except IntegrityError as e:
            logger.error(f"❌ Failed to create project: {e}")
            raise

    def get_project(self, project_id: str) -> Optional[Project]:
        """Obtiene proyecto por ID"""
        try:
            return Project.objects.get(id=uuid.UUID(project_id))
        except (Project.DoesNotExist, ValueError):
            return None

    def list_projects(
            self,
            status: str = None,
            limit: int = 50,
            offset: int = 0
    ) -> List[Project]:
        """Lista proyectos con filtros"""
        queryset = Project.objects.all()
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-updated_at")[offset:offset + limit]

    def delete_project(self, project_id: str) -> bool:
        """Elimina proyecto"""
        try:
            project = self.get_project(project_id)
            if project:
                project.delete()
                logger.info(f"Deleted project: {project_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete project: {e}")
            return False

    # ===========================================
    # CONVERSACIONES
    # ===========================================

    def create_conversation_session(
            self,
            project: Project,
            purpose: str,
            session_id: str = None
    ) -> ConversationSession:
        """Crea sesión de conversación"""
        return ConversationSession.objects.create(
            project=project,
            session_id=session_id or str(uuid.uuid4()),
            purpose=purpose
        )

    def add_message(
            self,
            session: ConversationSession,
            role: str,
            content: str,
            agent_type: str = None,
            intent: str = None,
            metadata: Dict[str, Any] = None,  # ✅ CORREGIDO: metadata: Dict[str, Any]
            related_tasks: List[int] = None
    ) -> Message:
        """Agrega un mensaje a la conversación"""
        message = Message.objects.create(
            session=session,
            role=role,
            content=content,
            agent_type=agent_type,
            intent=intent,
            metadata=metadata or {}  # ✅ Usar metadata (no meta)
        )

        # Relacionar con tareas si se especifica
        if related_tasks:
            for task_id in related_tasks:
                try:
                    task = Task.objects.get(id=task_id)
                    message.related_tasks.add(task)
                except Task.DoesNotExist:
                    pass

        return message


def get_conversation_history(
        self,
        session: ConversationSession,
        limit: int = 50,
        role: str = None
) -> List[Message]:
    """Obtiene historial de conversación"""
    queryset = Message.objects.filter(session=session)
    if role:
        queryset = queryset.filter(role=role)
    return queryset.order_by("created_at")[:limit]


def __repr__(self) -> str:
    return f"RelationalMemory(db={'SQLite' if USE_SQLITE else 'PostgreSQL'})"