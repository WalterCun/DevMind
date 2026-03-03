# devmind-core/db/models.py
"""
Modelos Django para DevMind Core.

Define la estructura de datos relacional para:
- Proyectos y su ciclo de vida
- Fases, tareas y dependencias
- Decisiones arquitectónicas (ADRs)
- Reportes de bugs y su resolución
- Historial de conversaciones
"""

from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField
import uuid


class Project(models.Model):
    """
    Representa un proyecto de desarrollo gestionado por DevMind.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, db_index=True)
    description = models.TextField(blank=True)

    # Estado del ciclo de vida
    STATUS_CHOICES = [
        ('discovery', '🔍 Discovery'),
        ('planning', '📋 Planning'),
        ('development', '💻 Development'),
        ('testing', '🧪 Testing'),
        ('maintenance', '🔧 Maintenance'),
        ('archived', '📦 Archived'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='discovery',
        db_index=True
    )

    # Configuración técnica
    tech_stack = JSONField(default=dict, blank=True)
    architecture = JSONField(default=dict, blank=True)
    constraints = JSONField(default=list, blank=True)

    # Planificación
    total_phases = models.IntegerField(default=0)
    current_phase = models.IntegerField(default=0)
    estimated_hours = models.FloatField(null=True, blank=True)
    viability_score = models.FloatField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_projects'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_status_display()})"


class ProjectPhase(models.Model):
    """
    Representa una fase dentro del ciclo de vida de un proyecto.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='phases'
    )
    phase_number = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)

    # Planificación
    goals = JSONField(default=list, blank=True)
    deliverables = JSONField(default=list, blank=True)
    estimated_hours = models.FloatField()
    actual_hours = models.FloatField(default=0)

    # Estado
    STATUS_CHOICES = [
        ('pending', '⏳ Pending'),
        ('in_progress', '🔄 In Progress'),
        ('completed', '✅ Completed'),
        ('blocked', '🚫 Blocked'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )

    # Fechas
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devmind_phases'
        ordering = ['phase_number']
        unique_together = ['project', 'phase_number']

    def __str__(self):
        return f"{self.project.name} - Fase {self.phase_number}: {self.name}"

    @property
    def progress_percent(self) -> float:
        """Calcula progreso basado en horas reales vs estimadas"""
        if self.estimated_hours == 0:
            return 100.0 if self.status == 'completed' else 0.0
        return min(100, (self.actual_hours / self.estimated_hours) * 100)


class Task(models.Model):
    """
    Representa una tarea atómica dentro de una fase.
    """
    phase = models.ForeignKey(
        ProjectPhase,
        on_delete=models.CASCADE,
        related_name='tasks'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Prioridad
    PRIORITY_CHOICES = [
        ('critical', '🔴 Critical'),
        ('high', '🟠 High'),
        ('medium', '🟡 Medium'),
        ('low', '🟢 Low'),
    ]
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        db_index=True
    )

    # Estado
    STATUS_CHOICES = [
        ('todo', 'Todo'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
        ('blocked', 'Blocked'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='todo',
        db_index=True
    )

    # Asignación
    assigned_agent = models.CharField(max_length=100, blank=True, db_index=True)

    # Dependencias (tareas que deben completarse antes)
    dependencies = models.ManyToManyField(
        'self',
        symmetrical=False,
        blank=True,
        related_name='dependents'
    )

    # Archivos afectados por esta tarea
    files_affected = JSONField(default=list, blank=True)

    # Métricas
    test_coverage = models.FloatField(default=0)
    estimated_minutes = models.IntegerField(null=True, blank=True)
    actual_minutes = models.IntegerField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devmind_tasks'
        ordering = ['-priority', 'created_at']
        indexes = [
            models.Index(fields=['phase', 'status']),
            models.Index(fields=['assigned_agent', 'status']),
        ]

    def __str__(self):
        return f"[{self.get_priority_display()}] {self.title}"

    @property
    def is_blocked(self) -> bool:
        """Verifica si la tarea está bloqueada por dependencias"""
        if self.status == 'blocked':
            return True
        return self.dependencies.exclude(status='done').exists()


class Decision(models.Model):
    """
    Registro de Decisión Arquitectónica (ADR - Architecture Decision Record).
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='decisions'
    )
    title = models.CharField(max_length=255)

    # Categoría de decisión
    CATEGORY_CHOICES = [
        ('architecture', 'Architecture'),
        ('technology', 'Technology'),
        ('pattern', 'Pattern'),
        ('constraint', 'Constraint'),
        ('tradeoff', 'Trade-off'),
    ]
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)

    # Contenido del ADR
    context = models.TextField(help_text="Situación que motivó la decisión")
    decision = models.TextField(help_text="Decisión tomada")
    consequences = models.TextField(help_text="Consecuencias positivas y negativas")
    alternatives_considered = JSONField(default=list, blank=True)

    # Estado
    STATUS_CHOICES = [
        ('proposed', 'Proposed'),
        ('accepted', 'Accepted'),
        ('deprecated', 'Deprecated'),
        ('superseded', 'Superseded'),
    ]
    status = models.CharField(max_length=20, default='accepted', choices=STATUS_CHOICES)

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.CharField(max_length=100, blank=True)  # Agente o usuario

    class Meta:
        db_table = 'devmind_decisions'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['project', 'category']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"ADR-{self.id}: {self.title}"


class BugReport(models.Model):
    """
    Reporte y seguimiento de bugs detectados.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='bugs'
    )
    title = models.CharField(max_length=255)
    description = models.TextField()

    # Severidad
    SEVERITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES)

    # Ubicación del bug
    file_path = models.CharField(max_length=500, blank=True)
    line_number = models.IntegerField(null=True, blank=True)
    error_log = models.TextField(blank=True)
    stack_trace = models.TextField(blank=True)

    # Estado del fix
    STATUS_CHOICES = [
        ('detected', '🔍 Detected'),
        ('analyzing', '🧠 Analyzing'),
        ('fixing', '🔧 Fixing'),
        ('testing_fix', '🧪 Testing Fix'),
        ('resolved', '✅ Resolved'),
        ('wont_fix', '❌ Won\'t Fix'),
    ]
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='detected',
        db_index=True
    )

    # Intentos de auto-fix
    fix_attempts = models.IntegerField(default=0)
    auto_fixed = models.BooleanField(default=False)
    fix_commit = models.CharField(max_length=100, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'devmind_bugs'
        ordering = ['-severity', '-created_at']
        indexes = [
            models.Index(fields=['project', 'status']),
            models.Index(fields=['file_path']),
        ]

    def __str__(self):
        return f"BUG-{self.id}: {self.title}"


class ConversationSession(models.Model):
    """
    Sesión de conversación entre usuario y agente.
    """
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='conversation_sessions'
    )
    session_id = models.UUIDField(unique=True, default=uuid.uuid4)
    purpose = models.CharField(max_length=255, help_text="Objetivo de la sesión")
    summary = models.TextField(blank=True, help_text="Resumen generado por el agente")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'devmind_conversation_sessions'
        ordering = ['-created_at']

    def __str__(self):
        return f"Session {self.session_id.hex[:8]} - {self.purpose[:50]}"


class Message(models.Model):
    """
    Mensaje individual dentro de una conversación.
    """
    session = models.ForeignKey(
        ConversationSession,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    # Rol del emisor
    ROLE_CHOICES = [
        ('user', 'User'),
        ('agent', 'Agent'),
        ('system', 'System'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    # Tipo de agente (si aplica)
    agent_type = models.CharField(max_length=100, blank=True)

    # Contenido
    content = models.TextField()
    intent = models.CharField(max_length=50, blank=True, db_index=True)

    # Metadata estructurada
    metadata = JSONField(default=dict, blank=True)

    # Relaciones con otras entidades
    related_tasks = models.ManyToManyField(Task, blank=True, related_name='messages')
    related_decisions = models.ManyToManyField(Decision, blank=True, related_name='messages')

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'devmind_messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['session', 'role']),
            models.Index(fields=['intent']),
        ]

    def __str__(self):
        return f"{self.role}: {self.content[:100]}..."