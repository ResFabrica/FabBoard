from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
import os
from fabusers.models import FabLab
from datetime import datetime

class MachineType(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nom")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    icon = models.CharField(max_length=50, default="fas fa-cog", verbose_name="Icône Font Awesome",
                          help_text="Classe CSS de l'icône Font Awesome (ex: fas fa-printer)")
    color = models.CharField(max_length=7, default="#007bff", verbose_name="Couleur",
                           help_text="Code couleur hexadécimal (ex: #007bff)")
    default_maintenance_period = models.IntegerField(default=30, verbose_name="Période de maintenance par défaut (jours)",
                                                   help_text="Nombre de jours par défaut entre les maintenances")
    requires_certification = models.BooleanField(default=False, verbose_name="Nécessite une certification",
                                               help_text="Indique si l'utilisation de ce type de machine nécessite une certification")
    safety_instructions = models.TextField(blank=True, null=True, verbose_name="Instructions de sécurité",
                                        help_text="Instructions de sécurité générales pour ce type de machine")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Type de machine"
        verbose_name_plural = "Types de machines"
        ordering = ['name']

class DefaultMaintenanceType(models.Model):
    """Maintenances par défaut pour un type de machine"""
    PRIORITY_CHOICES = [
        (1, 'Basse'),
        (2, 'Moyenne'),
        (3, 'Haute'),
        (4, 'Critique')
    ]

    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE, related_name='default_maintenances',
                                   verbose_name="Type de machine")
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(verbose_name="Description")
    period_days = models.IntegerField(null=True, blank=True, verbose_name="Périodicité (jours)")
    estimated_duration = models.DurationField(verbose_name="Durée estimée")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Priorité")
    instructions = models.TextField(verbose_name="Instructions")
    required_tools = models.TextField(blank=True, verbose_name="Outils nécessaires")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def __str__(self):
        return f"{self.name} - {self.machine_type.name}"

    class Meta:
        verbose_name = "Maintenance par défaut"
        verbose_name_plural = "Maintenances par défaut"
        ordering = ['-priority', 'name']

class MachineTemplate(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE, related_name='templates',
                                   verbose_name="Type de machine")
    manufacturer = models.CharField(max_length=100, verbose_name="Fabricant")
    model = models.CharField(max_length=100, verbose_name="Modèle")
    description = models.TextField(verbose_name="Description")
    documentation_url = models.URLField(blank=True, verbose_name="URL de la documentation")
    image = models.ImageField(upload_to='machine_templates/', blank=True, null=True, verbose_name="Image")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def __str__(self):
        return f"{self.manufacturer} {self.model}"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Si c'est un nouveau template, créer les maintenances par défaut
        if is_new:
            for default_maintenance in self.machine_type.default_maintenances.all():
                MaintenanceTemplate.objects.create(
                    machine_template=self,
                    name=default_maintenance.name,
                    description=default_maintenance.description,
                    period_days=default_maintenance.period_days,
                    estimated_duration=default_maintenance.estimated_duration,
                    priority=default_maintenance.priority,
                    instructions=default_maintenance.instructions,
                    required_tools=default_maintenance.required_tools
                )
        
        # Redimensionner l'image si nécessaire
        if self.image and hasattr(self.image, 'path') and os.path.exists(self.image.path):
            img = Image.open(self.image.path)
            
            # Convertir en RGB si nécessaire (pour les images PNG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionner si l'image est trop grande
            max_size = (800, 600)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            # Compresser et sauvegarder
            img.save(self.image.path, 'JPEG', quality=85, optimize=True)

    class Meta:
        verbose_name = "Template de machine"
        verbose_name_plural = "Templates de machines"
        ordering = ['manufacturer', 'model']

class MaintenanceTemplate(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Basse'),
        (2, 'Moyenne'),
        (3, 'Haute'),
        (4, 'Critique')
    ]

    machine_template = models.ForeignKey(MachineTemplate, on_delete=models.CASCADE,
                                       related_name='maintenance_templates',
                                       verbose_name="Template de machine")
    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(verbose_name="Description")
    period_days = models.IntegerField(null=True, blank=True, verbose_name="Périodicité (jours)")
    estimated_duration = models.DurationField(verbose_name="Durée estimée")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Priorité")
    instructions = models.TextField(verbose_name="Instructions")
    required_tools = models.TextField(blank=True, verbose_name="Outils nécessaires")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def __str__(self):
        return f"{self.name} - {self.machine_template}"

    class Meta:
        verbose_name = "Template de maintenance"
        verbose_name_plural = "Templates de maintenance"
        ordering = ['-priority', 'name']

class Machine(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE, verbose_name="Type de machine")
    template = models.ForeignKey(MachineTemplate, on_delete=models.SET_NULL, null=True, blank=True,
                               verbose_name="Template utilisé")
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE, verbose_name="FabLab")
    serial_number = models.CharField(max_length=100, blank=True, null=True, verbose_name="Numéro de série")
    image = models.ImageField(upload_to='machine_images/', null=True, blank=True, verbose_name="Image")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")
    
    def __str__(self):
        return f"{self.name} ({self.fablab.name})"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        if self.image and hasattr(self.image, 'path') and os.path.exists(self.image.path):
            img = Image.open(self.image.path)
            
            # Convertir en RGB si nécessaire (pour les images PNG)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            
            # Redimensionner si l'image est trop grande
            max_size = (800, 600)
            if img.size[0] > max_size[0] or img.size[1] > max_size[1]:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
            # Compresser et sauvegarder
            img.save(self.image.path, 'JPEG', quality=85, optimize=True)

    class Meta:
        verbose_name = "Machine"
        verbose_name_plural = "Machines"
        ordering = ['name']
        unique_together = ['name', 'fablab']  # Contrainte d'unicité sur le nom dans un FabLab

class MaintenanceType(models.Model):
    PRIORITY_CHOICES = [
        (1, 'Basse'),
        (2, 'Moyenne'),
        (3, 'Haute'),
        (4, 'Critique')
    ]

    name = models.CharField(max_length=100, verbose_name="Nom")
    period_days = models.IntegerField(null=True, blank=True, verbose_name="Périodicité (jours)")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    is_custom = models.BooleanField(default=False, verbose_name="Personnalisé")
    priority = models.IntegerField(choices=PRIORITY_CHOICES, default=2, verbose_name="Priorité")
    instructions = models.TextField(blank=True, null=True, verbose_name="Instructions")
    required_tools = models.TextField(blank=True, null=True, verbose_name="Outils nécessaires")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")
    
    def __str__(self):
        return self.name

    def get_priority_display(self):
        return dict(self.PRIORITY_CHOICES).get(self.priority, '')

    class Meta:
        verbose_name = "Type de maintenance"
        verbose_name_plural = "Types de maintenance"
        ordering = ['name']

class Maintenance(models.Model):
    SCHEDULING_TYPES = [
        ('today', 'Aujourd\'hui'),
        ('scheduled', 'Planifiée'),
        ('periodic', 'Périodique'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Machine")
    maintenance_type = models.ForeignKey(MaintenanceType, on_delete=models.CASCADE, verbose_name="Type de maintenance")
    scheduled_date = models.DateField(verbose_name="Date prévue")
    completed_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de réalisation")
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                   verbose_name="Réalisée par")
    notes = models.TextField(blank=True, verbose_name="Notes")
    scheduling_type = models.CharField(max_length=10, choices=SCHEDULING_TYPES, default='scheduled',
                                     verbose_name="Type de programmation")
    period_days = models.IntegerField(null=True, blank=True, verbose_name="Périodicité (jours)")
    custom_type_name = models.CharField(max_length=100, blank=True, null=True,
                                      verbose_name="Nom personnalisé")
    significant = models.BooleanField(default=False, verbose_name="Maintenance marquante",
                                    help_text="Indique si cette maintenance est marquante")
    instructions = models.TextField(blank=True, null=True, verbose_name="Instructions")
    required_tools = models.TextField(blank=True, null=True, verbose_name="Outils nécessaires")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def is_due_soon(self):
        if self.completed_date:
            return False
        # Convertir scheduled_date en datetime aware
        scheduled_datetime = timezone.make_aware(
            datetime.combine(self.scheduled_date, datetime.min.time())
        )
        return scheduled_datetime <= timezone.now() + timezone.timedelta(days=7)

    def __str__(self):
        return f"{self.maintenance_type.name} - {self.machine.name}"

    class Meta:
        verbose_name = "Maintenance"
        verbose_name_plural = "Maintenances"
        ordering = ['scheduled_date']
