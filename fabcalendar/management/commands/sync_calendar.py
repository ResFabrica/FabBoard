from django.core.management.base import BaseCommand
from fabprojects.models import Task
from fabmaintenance.models import Maintenance
from fabcalendar.signals import sync_task_to_calendar, sync_maintenance_to_calendar
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Synchronise les tâches et maintenances existantes avec le calendrier'

    def handle(self, *args, **options):
        # Synchroniser les tâches
        tasks = Task.objects.exclude(deadline=None)
        self.stdout.write(f"Synchronisation de {tasks.count()} tâches...")
        for task in tasks:
            try:
                sync_task_to_calendar(Task, task, False)
                self.stdout.write(self.style.SUCCESS(f"Tâche {task.id} synchronisée"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la synchronisation de la tâche {task.id}: {e}"))

        # Synchroniser les maintenances
        maintenances = Maintenance.objects.exclude(scheduled_date=None)
        self.stdout.write(f"Synchronisation de {maintenances.count()} maintenances...")
        for maintenance in maintenances:
            try:
                sync_maintenance_to_calendar(Maintenance, maintenance, False)
                self.stdout.write(self.style.SUCCESS(f"Maintenance {maintenance.id} synchronisée"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Erreur lors de la synchronisation de la maintenance {maintenance.id}: {e}"))

        self.stdout.write(self.style.SUCCESS("Synchronisation terminée")) 