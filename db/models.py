from django.db import models
from django.contrib.postgres.fields import JSONField
import uuid

class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=255)
    description = models.TextField()
    status = models.CharField(
        max_length=30,
        choices=[
            ('discovery', 'Discovery'),
            ('planning', 'Planning'),
            ('development', 'Development'),
            ('testing', 'Testing'),
            ('maintenance', 'Maintenance'),
            ('archived', 'Archived')
        ],
        default='discovery'
    )
    tech_stack = JSONField(default=dict)
    viability_score = models.FloatField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class ProjectPhase(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    phase_number = models.IntegerField()
    name = models.CharField(max_length=255)
    description = models.TextField()
    goals = JSONField(default=list)
    deliverables = JSONField(default=list)
    estimated_hours = models.FloatField()
    actual_hours = models.FloatField(default=0)
    status = models.CharField(
        max_length=30,
        choices=[
            ('pending', 'Pending'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('blocked', 'Blocked')
        ],
        default='pending'
    )

class Task(models.Model):
    phase = models.ForeignKey(ProjectPhase, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField()
    priority = models.CharField(
        max_length=20,
        choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    )
    status = models.CharField(
        max_length=30,
        choices=[
            ('todo', 'Todo'),
            ('in_progress', 'In Progress'),
            ('review', 'Review'),
            ('done', 'Done'),
            ('blocked', 'Blocked')
        ],
        default='todo'
    )
    assigned_agent = models.CharField(max_length=100, blank=True)
    files_affected = JSONField(default=list)

class Decision(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='decisions')
    title = models.CharField(max_length=255)
    category = models.CharField(
        max_length=50,
        choices=[
            ('architecture', 'Architecture'),
            ('technology', 'Technology'),
            ('pattern', 'Pattern'),
            ('constraint', 'Constraint'),
            ('tradeoff', 'Trade-off')
        ]
    )
    context = models.TextField()
    decision = models.TextField()
    consequences = models.TextField()
    status = models.CharField(max_length=20, default='accepted')

class BugReport(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='bugs')
    title = models.CharField(max_length=255)
    description = models.TextField()
    severity = models.CharField(
        max_length=20,
        choices=[('critical', 'Critical'), ('high', 'High'), ('medium', 'Medium'), ('low', 'Low')]
    )
    file_path = models.CharField(max_length=500)
    status = models.CharField(
        max_length=30,
        choices=[
            ('detected', 'Detected'),
            ('analyzing', 'Analyzing'),
            ('fixing', 'Fixing'),
            ('testing_fix', 'Testing Fix'),
            ('resolved', 'Resolved'),
            ('wont_fix', 'Won\'t Fix')
        ],
        default='detected'
    )
    auto_fixed = models.BooleanField(default=False)
    fix_attempts = models.IntegerField(default=0)