from django.db import models
from django.contrib.auth.models import User
from fabusers.models import FabLab
import os
import logging

logger = logging.getLogger(__name__)

class View(models.Model):
    name = models.CharField(max_length=200)
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE, related_name='project_views')
    custom_fields = models.ManyToManyField('CustomField', related_name='views', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.fablab.name}"

    class Meta:
        ordering = ['name']

class Section(models.Model):
    name = models.CharField(max_length=200)
    view = models.ForeignKey(View, on_delete=models.CASCADE, related_name='sections')
    order = models.IntegerField(default=0)
    tags = models.ManyToManyField('Tag', blank=True, related_name='sections')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['order', 'name']

class Tag(models.Model):
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=7)  # Format: #RRGGBB
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE, related_name='project_tags')

    def __str__(self):
        return self.name

class CustomField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Boolean'),
        ('choice', 'Choice'),
    ]

    name = models.CharField(max_length=100)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    choices = models.TextField(blank=True, null=True)  # Pour le type 'choice', stocké en JSON
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE, related_name='custom_fields')

    def __str__(self):
        return f"{self.name} ({self.get_field_type_display()})"

class Task(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='tasks')
    view = models.ForeignKey(View, on_delete=models.CASCADE, related_name='tasks', null=True)
    assigned_users = models.ManyToManyField(User, related_name='assigned_tasks', blank=True)
    deadline = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='tasks', blank=True)
    is_completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    @property
    def display_title(self):
        has_files = self.files.exists()
        return f"{self.title} 📎" if has_files else self.title

    def save(self, *args, **kwargs):
        if not self.view_id and self.section_id:
            self.view = self.section.view
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-created_at', 'order', 'deadline']

class SubTask(models.Model):
    title = models.CharField(max_length=200)
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='subtasks')
    is_completed = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['order', 'created_at']

class CustomFieldValue(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='custom_field_values')
    field = models.ForeignKey(CustomField, on_delete=models.CASCADE)
    value = models.TextField()

    def __str__(self):
        return f"{self.field.name}: {self.value}"

class TaskFile(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='task_files/')
    filename = models.CharField(max_length=255)
    file_type = models.CharField(max_length=50)
    file_size = models.IntegerField()  # Taille en bytes
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename

    def save(self, *args, **kwargs):
        if not self.filename and self.file:
            self.filename = self.file.name
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.file:
            file_path = self.file.path if hasattr(self.file, 'path') else None
            try:
                if file_path and os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass
        super().delete(*args, **kwargs)
