# devmind-core/core/memory/relational_store.py
"""
Memoria relacional para DevMind Core usando PostgreSQL.

Proporciona almacenamiento estructurado para:
- Estado de proyectos y fases
- Tareas y su progreso
- Decisiones y bugs
- Métricas y auditoría
"""

import os
import logging
from typing import List, Dict, Any, Optional, TypeVar, Generic
from datetime import datetime
from enum import Enum
from contextlib import contextmanager
import uuid

# Configurar Django settings ANTES de importar modelos
if not os.environ.get("DJANGO_SETTINGS_MODULE"):
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "db.settings")

import django

django.setup()

from django.db import models, transaction, IntegrityError
from django.db.models import Q, Count, Avg, F
from db.models import (
    Project, ProjectPhase, Task, Decision, BugReport,
    ConversationSession, Message
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


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
    Memoria relacional basada en PostgreSQL para estado estructurado.

    Características:
    - CRUD completo para entidades del proyecto
    - Consultas complejas con Django ORM
    - Transacciones atómicas
    - Métricas y agregaciones
    - Historial de conversaciones
    """

    def __init__(self, db_url: str = None):
        """
        Inicializa la memoria relacional.

        Args:
            db_url: URL de conexión a PostgreSQL (usa env var si None)
        """
        self.db_url = db_url or os.getenv("DATABASE_URL")
        logger.info("RelationalMemory initialized")

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
            logger.info(f"Created project: {project.id} - {name}")
            return project
        except IntegrityError as e:
            logger.error(f"Failed to create project: {e}")
            raise

    def get_project(self, project_id: str) -> Optional[Project]:
        """Obtiene proyecto por ID"""
        try:
            return Project.objects.get(id=uuid.UUID(project_id))
        except (Project.DoesNotExist, ValueError):
            return None

    def update_project(self, project_id: str, **updates) -> Optional[Project]:
        """Actualiza campos de un proyecto"""
        project = self.get_project(project_id)
        if not project:
            return None

        for key, value in updates.items():
            if hasattr(project, key):
                setattr(project, key, value)

        project.updated_at = datetime.now()
        project.save()
        logger.debug(f"Updated project: {project_id}")
        return project

    def list_projects(
            self,
            status: str = None,
            limit: int = 50,
            offset: int = 0
    ) -> List[Project]:
        """Lista proyectos con filtros opcionales"""
        queryset = Project.objects.all()

        if status:
            queryset = queryset.filter(status=status)

        return queryset.order_by("-updated_at")[offset:offset + limit]

    def delete_project(self, project_id: str) -> bool:
        """Elimina proyecto y sus datos asociados (cascada)"""
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
    # FASES DEL PROYECTO
    # ===========================================

    def create_phase(
            self,
            project: Project,
            name: str,
            description: str,
            phase_number: int,
            estimated_hours: float,
            goals: List[str] = None,
            deliverables: List[str] = None,
            **kwargs
    ) -> ProjectPhase:
        """Crea una fase de proyecto"""
        return ProjectPhase.objects.create(
            project=project,
            name=name,
            description=description,
            phase_number=phase_number,
            estimated_hours=estimated_hours,
            goals=goals or [],
            deliverables=deliverables or [],
            **kwargs
        )

    def get_phase(self, phase_id: int) -> Optional[ProjectPhase]:
        """Obtiene fase por ID"""
        try:
            return ProjectPhase.objects.get(id=phase_id)
        except ProjectPhase.DoesNotExist:
            return None

    def list_phases(self, project: Project, status: str = None) -> List[ProjectPhase]:
        """Lista fases de un proyecto"""
        queryset = ProjectPhase.objects.filter(project=project)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("phase_number")

    def update_phase_progress(
            self,
            phase: ProjectPhase,
            actual_hours: float = None,
            status: str = None
    ) -> ProjectPhase:
        """Actualiza progreso de una fase"""
        if actual_hours is not None:
            phase.actual_hours = actual_hours
        if status:
            phase.status = status

        phase.save()
        return phase

    # ===========================================
    # TAREAS
    # ===========================================

    def create_task(
            self,
            phase: ProjectPhase,
            title: str,
            description: str,
            priority: str,
            assigned_agent: str = None,
            dependencies: List[int] = None,
            files_affected: List[str] = None,
            **kwargs
    ) -> Task:
        """Crea una nueva tarea"""
        task = Task.objects.create(
            phase=phase,
            title=title,
            description=description,
            priority=priority,
            assigned_agent=assigned_agent,
            files_affected=files_affected or [],
            **kwargs
        )

        # Establecer dependencias si existen
        if dependencies:
            for dep_id in dependencies:
                try:
                    dep_task = Task.objects.get(id=dep_id)
                    task.dependencies.add(dep_task)
                except Task.DoesNotExist:
                    logger.warning(f"Dependency task {dep_id} not found")

        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        """Obtiene tarea por ID"""
        try:
            return Task.objects.prefetch_related("dependencies").get(id=task_id)
        except Task.DoesNotExist:
            return None

    def list_tasks(
            self,
            phase: ProjectPhase = None,
            project: Project = None,
            status: str = None,
            priority: str = None,
            assigned_agent: str = None,
            limit: int = 100
    ) -> List[Task]:
        """Lista tareas con múltiples filtros"""
        queryset = Task.objects.all()

        if project:
            queryset = queryset.filter(phase__project=project)
        elif phase:
            queryset = queryset.filter(phase=phase)

        if status:
            queryset = queryset.filter(status=status)
        if priority:
            queryset = queryset.filter(priority=priority)
        if assigned_agent:
            queryset = queryset.filter(assigned_agent=assigned_agent)

        return queryset.order_by("-priority", "-created_at")[:limit]

    def update_task_status(self, task: Task, status: str) -> Task:
        """Actualiza estado de una tarea"""
        task.status = status
        if status == "done":
            task.completed_at = datetime.now()
        task.save()
        return task

    def get_blocked_tasks(self, project: Project) -> List[Task]:
        """Obtiene tareas bloqueadas por dependencias"""
        return Task.objects.filter(
            phase__project=project,
            status__in=["todo", "in_progress"],
            dependencies__status__in=["todo", "in_progress", "blocked"]
        ).distinct()

    # ===========================================
    # DECISIONES Y BUGS
    # ===========================================

    def record_decision(
            self,
            project: Project,
            title: str,
            category: str,
            decision: str,
            context: str = "",
            consequences: str = "",
            alternatives: List[str] = None
    ) -> Decision:
        """Registra una decisión arquitectónica"""
        return Decision.objects.create(
            project=project,
            title=title,
            category=category,
            context=context,
            decision=decision,
            consequences=consequences,
            alternatives_considered=alternatives or []
        )

    def list_decisions(
            self,
            project: Project,
            category: str = None,
            status: str = None
    ) -> List[Decision]:
        """Lista decisiones del proyecto"""
        queryset = Decision.objects.filter(project=project)
        if category:
            queryset = queryset.filter(category=category)
        if status:
            queryset = queryset.filter(status=status)
        return queryset.order_by("-created_at")

    def report_bug(
            self,
            project: Project,
            title: str,
            description: str,
            severity: str,
            file_path: str = None,
            error_log: str = None,
            stack_trace: str = None
    ) -> BugReport:
        """Reporta un nuevo bug"""
        return BugReport.objects.create(
            project=project,
            title=title,
            description=description,
            severity=severity,
            file_path=file_path,
            error_log=error_log,
            stack_trace=stack_trace
        )

    def update_bug_status(
            self,
            bug: BugReport,
            status: str,
            fix_commit: str = None,
            auto_fixed: bool = None
    ) -> BugReport:
        """Actualiza estado de un bug"""
        bug.status = status
        if fix_commit:
            bug.fix_commit = fix_commit
        if auto_fixed is not None:
            bug.auto_fixed = auto_fixed
            if auto_fixed:
                bug.fix_attempts = F("fix_attempts") + 1
        if status == "resolved":
            bug.resolved_at = datetime.now()
        bug.save()
        return bug

    # ===========================================
    # CONVERSACIONES
    # ===========================================

    def create_conversation_session(
            self,
            project: Project,
            purpose: str,
            session_id: str = None
    ) -> ConversationSession:
        """Crea una nueva sesión de conversación"""
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
            metadata: Dict = None,
            related_tasks: List[int] = None
    ) -> Message:
        """Agrega un mensaje a la conversación"""
        message = Message.objects.create(
            session=session,
            role=role,
            content=content,
            agent_type=agent_type,
            intent=intent,
            metadata=metadata or {}
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

    # ===========================================
    # MÉTRICAS Y REPORTES
    # ===========================================

    def get_project_metrics(self, project: Project) -> Dict[str, Any]:
        """Obtiene métricas consolidadas del proyecto"""
        phases = ProjectPhase.objects.filter(project=project)
        tasks = Task.objects.filter(phase__project=project)
        bugs = BugReport.objects.filter(project=project)

        return {
            "project_id": str(project.id),
            "name": project.name,
            "status": project.status,
            "phases": {
                "total": phases.count(),
                "completed": phases.filter(status="completed").count(),
                "progress_percent": self._calculate_phase_progress(phases)
            },
            "tasks": {
                "total": tasks.count(),
                "by_status": {
                    status: tasks.filter(status=status).count()
                    for status in ["todo", "in_progress", "review", "done", "blocked"]
                },
                "by_priority": {
                    priority: tasks.filter(priority=priority).count()
                    for priority in ["critical", "high", "medium", "low"]
                }
            },
            "bugs": {
                "total": bugs.count(),
                "open": bugs.exclude(status="resolved").count(),
                "resolved": bugs.filter(status="resolved").count(),
                "auto_fixed": bugs.filter(auto_fixed=True).count()
            },
            "decisions": Decision.objects.filter(project=project).count(),
            "viability_score": project.viability_score
        }

    def _calculate_phase_progress(self, phases) -> float:
        """Calcula progreso porcentual basado en fases"""
        if not phases:
            return 0.0

        total_estimated = sum(p.estimated_hours for p in phases)
        if total_estimated == 0:
            return 100.0 if all(p.status == "completed" for p in phases) else 0.0

        total_actual = sum(p.actual_hours for p in phases)
        completed = sum(1 for p in phases if p.status == "completed")

        # Combinar métricas de tiempo y estado
        time_progress = min(100, (total_actual / total_estimated) * 100)
        status_progress = (completed / phases.count()) * 100

        return round((time_progress + status_progress) / 2, 1)

    def get_agent_performance(
            self,
            agent_name: str,
            project: Project = None,
            days: int = 30
    ) -> Dict[str, Any]:
        """Obtiene métricas de rendimiento de un agente"""
        from django.utils import timezone
        from datetime import timedelta

        cutoff = timezone.now() - timedelta(days=days)

        # Tareas asignadas al agente
        tasks = Task.objects.filter(
            assigned_agent=agent_name,
            created_at__gte=cutoff
        )
        if project:
            tasks = tasks.filter(phase__project=project)

        return {
            "agent": agent_name,
            "period_days": days,
            "tasks_assigned": tasks.count(),
            "tasks_completed": tasks.filter(status="done").count(),
            "completion_rate": round(
                tasks.filter(status="done").count() / max(1, tasks.count()) * 100, 1
            ),
            "avg_time_to_complete": None  # Implementar si hay timestamps de inicio/fin
        }

    def search(
            self,
            project: Project,
            query: str,
            entities: List[str] = None,
            limit: int = 20
    ) -> Dict[str, List[Any]]:
        """
        Búsqueda full-text en entidades del proyecto.

        Args:
            project: Proyecto a buscar
            query: Término de búsqueda
            entities: Entidades a incluir (tasks, decisions, bugs, messages)
            limit: Máximo resultados por entidad

        Returns:
            Diccionario con resultados agrupados por entidad
        """
        from django.db.models import Q

        entities = entities or ["tasks", "decisions", "bugs", "messages"]
        results = {}

        # === FIX: Q objects deben ir antes de keyword args o usar filter encadenado ===

        # Búsqueda en tareas
        if "tasks" in entities:
            results["tasks"] = list(Task.objects.filter(
                phase__project=project
            ).filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:limit])

        # Búsqueda en decisiones
        if "decisions" in entities:
            results["decisions"] = list(Decision.objects.filter(
                project=project
            ).filter(
                Q(title__icontains=query) | Q(decision__icontains=query)
            )[:limit])

        # Búsqueda en bugs
        if "bugs" in entities:
            results["bugs"] = list(BugReport.objects.filter(
                project=project
            ).filter(
                Q(title__icontains=query) | Q(description__icontains=query)
            )[:limit])

        # Búsqueda en mensajes
        if "messages" in entities:
            results["messages"] = list(Message.objects.filter(
                session__project=project
            ).filter(
                Q(content__icontains=query)
            )[:limit])

        return results

    def __repr__(self) -> str:
        return f"RelationalMemory(db={self.db_url[:30] if self.db_url else 'default'}...)"