from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from fabprojects.models import Task
from fabmaintenance.models import Maintenance
from .models import CalendarEvent
from django.utils import timezone
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Task)
def sync_task_to_calendar(sender, instance, created, **kwargs):
    """Synchronise une tâche avec le calendrier."""
    if instance.deadline:
        content_type = ContentType.objects.get_for_model(Task)
        # Convertir la date en datetime aware
        deadline = timezone.make_aware(instance.deadline) if timezone.is_naive(instance.deadline) else instance.deadline
        
        event, created = CalendarEvent.objects.get_or_create(
            content_type=content_type,
            object_id=instance.id,
            defaults={
                'title': instance.title,
                'description': instance.description,
                'start_date': deadline,
                'end_date': deadline,  # Pour une tâche, début et fin sont identiques
                'event_type': 'task',
                'fablab': instance.section.view.fablab,
                'created_by': instance.assigned_users.first() if instance.assigned_users.exists() else None,
                'allday': True  # Les tâches sont toujours sur toute la journée
            }
        )
        
        if not created:
            event.title = instance.title
            event.description = instance.description
            event.start_date = deadline
            event.end_date = deadline
            event.allday = True
            event.save()
            
            # Mise à jour des utilisateurs assignés
            event.assigned_users.set(instance.assigned_users.all())
        
        logger.info(f"Tâche synchronisée avec le calendrier : {event}")

@receiver(post_save, sender=Maintenance)
def sync_maintenance_to_calendar(sender, instance, created, **kwargs):
    """Synchronise une maintenance avec le calendrier."""
    content_type = ContentType.objects.get_for_model(Maintenance)
    
    # Si la maintenance est complétée, supprimer l'événement du calendrier
    if instance.completed_date:
        CalendarEvent.objects.filter(
            content_type=content_type,
            object_id=instance.id
        ).delete()
        logger.info(f"Événement du calendrier supprimé pour la maintenance {instance.id} (complétée)")
        return
    
    # Convertir la date en datetime aware
    if isinstance(instance.scheduled_date, datetime):
        scheduled_date = timezone.make_aware(instance.scheduled_date) if timezone.is_naive(instance.scheduled_date) else instance.scheduled_date
    else:
        # Si c'est une date (pas un datetime), convertir en datetime à minuit
        scheduled_date = timezone.make_aware(datetime.combine(instance.scheduled_date, datetime.min.time()))
    
    event, created = CalendarEvent.objects.get_or_create(
        content_type=content_type,
        object_id=instance.id,
        defaults={
            'title': f"{instance.maintenance_type.name} - {instance.machine.name}",
            'description': instance.notes,
            'start_date': scheduled_date,
            'end_date': scheduled_date,  # Pour une maintenance, début et fin sont identiques
            'event_type': 'maintenance',
            'fablab': instance.machine.fablab,
            'created_by': instance.completed_by,
            'allday': True  # Les maintenances sont toujours sur toute la journée
        }
    )
    
    if not created:
        event.title = f"{instance.maintenance_type.name} - {instance.machine.name}"
        event.description = instance.notes
        event.start_date = scheduled_date
        event.end_date = scheduled_date
        event.allday = True
        event.save()
    
    logger.info(f"Maintenance synchronisée avec le calendrier : {event}")

@receiver(post_delete, sender=Task)
def delete_task_calendar_event(sender, instance, **kwargs):
    """Supprime l'événement du calendrier associé à une tâche supprimée."""
    content_type = ContentType.objects.get_for_model(Task)
    CalendarEvent.objects.filter(
        content_type=content_type,
        object_id=instance.id
    ).delete()
    logger.info(f"Événement du calendrier supprimé pour la tâche {instance.id}")

@receiver(post_delete, sender=Maintenance)
def delete_maintenance_calendar_event(sender, instance, **kwargs):
    """Supprime l'événement du calendrier associé à une maintenance supprimée."""
    content_type = ContentType.objects.get_for_model(Maintenance)
    CalendarEvent.objects.filter(
        content_type=content_type,
        object_id=instance.id
    ).delete()
    logger.info(f"Événement du calendrier supprimé pour la maintenance {instance.id}") 