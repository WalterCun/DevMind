# devmind-core/db/models.py
"""
Modelos Django para DevMind Core.
Almacena estado estructurado de proyectos, tareas y decisiones.
Compatible con PostgreSQL y SQLite.
"""

import uuid

from django.db import models


# ✅ CORREGIDO: Usar models.JSONField (compatible con todos los backends)
# NO usar: from django.contrib.postgres.fields import JSONField  ← OBSOLETO


class Project(models.Model):
    """Proyecto principal"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # ✅ CORREGIDO: models.JSONField en lugar de postgres.fields.JSONField
    tech_stack = models.JSONField(default=dict, blank=True)
    architecture = models.JSONField(default=dict, blank=True)
    constraints = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('planning', 'Planning'),
            ('active', 'Active'),
            ('paused', 'Paused'),
            ('completed', 'Completed'),
            ('archived', 'Archived'),
        ],
        default='planning'
    )
    viability_score = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_projects'
        ordering = ['-updated_at']

    def __str__(self):
        return self.name


class ProjectPhase(models.Model):
    """Fase de proyecto"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=100)
    description = models.TextField()
    phase_number = models.IntegerField()

    # ✅ CORREGIDO: models.JSONField
    goals = models.JSONField(default=list, blank=True)
    deliverables = models.JSONField(default=list, blank=True)

    estimated_hours = models.FloatField()
    actual_hours = models.FloatField(default=0)

    status = models.CharField(
        max_length=20,
        choices=[
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('completed', 'Completed'),
            ('blocked', 'Blocked'),
        ],
        default='todo'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_project_phases'
        ordering = ['phase_number']
        unique_together = ['project', 'phase_number']


class Task(models.Model):
    """Tarea individual"""
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=200)
    description = models.TextField()

    priority = models.CharField(
        max_length=10,
        choices=[
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('todo', 'To Do'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('done', 'Done'),
            ('blocked', 'Blocked'),
        ],
        default='todo'
    )

    assigned_agent = models.CharField(max_length=100, blank=True)

    # ✅ CORREGIDO: models.JSONField
    files_affected = models.JSONField(default=list, blank=True)

    dependencies = models.ManyToManyField('self', symmetrical=False, blank=True)

    estimated_hours = models.FloatField(null=True, blank=True)
    actual_hours = models.FloatField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devmind_tasks'
        ordering = ['-priority', '-created_at']


class Decision(models.Model):
    """Decisión arquitectónica (ADR)"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='decisions')
    title = models.CharField(max_length=200)
    category = models.CharField(max_length=50)
    context = models.TextField(blank=True)
    decision = models.TextField()
    consequences = models.TextField(blank=True)

    # ✅ CORREGIDO: models.JSONField
    alternatives_considered = models.JSONField(default=list, blank=True)

    status = models.CharField(
        max_length=20,
        choices=[
            ('proposed', 'Proposed'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('deprecated', 'Deprecated'),
            ('superseded', 'Superseded'),
        ],
        default='proposed'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_decisions'
        ordering = ['-created_at']


class BugReport(models.Model):
    """Reporte de bug"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bugs')
    title = models.CharField(max_length=200)
    description = models.TextField()

    severity = models.CharField(
        max_length=20,
        choices=[
            ('critical', 'Critical'),
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        default='medium'
    )

    status = models.CharField(
        max_length=20,
        choices=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('wont_fix', "Won't Fix"),
        ],
        default='open'
    )

    file_path = models.CharField(max_length=500, blank=True)
    error_log = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)

    fix_commit = models.CharField(max_length=100, blank=True)
    fix_attempts = models.IntegerField(default=0)
    auto_fixed = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devmind_bugs'
        ordering = ['-severity', '-created_at']


class ConversationSession(models.Model):
    """Sesión de conversación"""
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='conversations')
    session_id = models.CharField(max_length=100, unique=True)
    purpose = models.CharField(max_length=200)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_conversations'


class Message(models.Model):
    """Mensaje en conversación"""
    session = models.ForeignKey(ConversationSession, on_delete=models.CASCADE, related_name='messages')

    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()

    agent_type = models.CharField(max_length=100, blank=True)
    intent = models.CharField(max_length=50, blank=True)

    # ✅ CORREGIDO: models.JSONField
    metadata = models.JSONField(default=dict, blank=True)

    related_tasks = models.ManyToManyField(Task, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devmind_messages'
        ordering = ['created_at']