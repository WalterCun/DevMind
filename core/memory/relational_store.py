import os
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'db.settings')
django.setup()

from db.models import Project, ProjectPhase, Task, Decision, BugReport
from typing import List, Optional, Dict, Any
import uuid


class RelationalMemory:
    """Memoria relacional para estado estructurado"""

    def __init__(self):
        pass

    def create_project(self, name: str, description: str) -> Project:
        """Crea un nuevo proyecto"""
        return Project.objects.create(
            name=name,
            description=description
        )

    def get_project(self, project_id: str) -> Optional[Project]:
        """Obtiene proyecto por ID"""
        try:
            return Project.objects.get(id=uuid.UUID(project_id))
        except Project.DoesNotExist:
            return None

    def create_phase(self, project: Project, phase_data: Dict) -> ProjectPhase:
        """Crea una fase de proyecto"""
        return ProjectPhase.objects.create(
            project=project,
            **phase_data
        )

    def create_task(self, phase: ProjectPhase, task_data: Dict) -> Task:
        """Crea una tarea"""
        return Task.objects.create(
            phase=phase,
            **task_data
        )

    def record_decision(self, project: Project, decision_data: Dict) -> Decision:
        """Registra una decisión arquitectónica"""
        return Decision.objects.create(
            project=project,
            **decision_data
        )

    def report_bug(self, project: Project, bug_data: Dict) -> BugReport:
        """Reporta un bug"""
        return BugReport.objects.create(
            project=project,
            **bug_data
        )

    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Obtiene estado completo del proyecto"""
        project = self.get_project(project_id)
        if not project:
            return None

        return {
            'project': {
                'id': str(project.id),
                'name': project.name,
                'status': project.status,
                'viability_score': project.viability_score
            },
            'phases': [
                {
                    'id': p.id,
                    'name': p.name,
                    'status': p.status,
                    'progress': (p.actual_hours / p.estimated_hours * 100) if p.estimated_hours > 0 else 0
                }
                for p in project.phases.all()
            ],
            'tasks': {
                'total': Task.objects.filter(phase__project=project).count(),
                'done': Task.objects.filter(phase__project=project, status='done').count(),
                'in_progress': Task.objects.filter(phase__project=project, status='in_progress').count()
            },
            'bugs': {
                'open': BugReport.objects.filter(project=project).exclude(status='resolved').count(),
                'resolved': BugReport.objects.filter(project=project, status='resolved').count()
            }
        }