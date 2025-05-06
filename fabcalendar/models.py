from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from fabusers.models import FabLab

class CalendarEvent(models.Model):
    EVENT_TYPES = [
        ('task', 'Tâche'),
        ('maintenance', 'Maintenance'),
        ('custom', 'Événement personnalisé'),
    ]

    title = models.CharField(max_length=200, verbose_name="Titre")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    start_date = models.DateTimeField(verbose_name="Date de début")
    end_date = models.DateTimeField(verbose_name="Date de fin")
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES, verbose_name="Type d'événement")
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE, verbose_name="FabLab")
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_events')
    assigned_users = models.ManyToManyField(User, related_name='assigned_events', blank=True)
    allday = models.BooleanField(default=False, verbose_name="Événement sur toute la journée")
    
    # Pour lier l'événement à un objet spécifique (Task, Maintenance, etc.)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.title} ({self.get_event_type_display()})"
    
    class Meta:
        verbose_name = "Événement du calendrier"
        verbose_name_plural = "Événements du calendrier"
        ordering = ['start_date'] 