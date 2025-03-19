from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from PIL import Image
import os
from fabusers.models import FabLab

class MachineType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Machine(models.Model):
    name = models.CharField(max_length=100)
    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE)
    fablab = models.ForeignKey(FabLab, on_delete=models.CASCADE)
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    image = models.ImageField(upload_to='machine_images/', null=True, blank=True)
    
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

class MaintenanceType(models.Model):
    name = models.CharField(max_length=100)
    machine_type = models.ForeignKey(MachineType, on_delete=models.CASCADE)
    period_days = models.IntegerField(null=True, blank=True)
    description = models.TextField(blank=True, null=True)
    is_custom = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.name} ({self.machine_type.name})"

class Maintenance(models.Model):
    SCHEDULING_TYPES = [
        ('today', 'Aujourd\'hui'),
        ('scheduled', 'Planifiée'),
        ('periodic', 'Périodique'),
    ]

    machine = models.ForeignKey(Machine, on_delete=models.CASCADE)
    maintenance_type = models.ForeignKey(MaintenanceType, on_delete=models.CASCADE)
    scheduled_date = models.DateTimeField()
    completed_date = models.DateTimeField(null=True, blank=True)
    completed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    scheduling_type = models.CharField(max_length=10, choices=SCHEDULING_TYPES, default='scheduled')
    period_days = models.IntegerField(null=True, blank=True)
    custom_type_name = models.CharField(max_length=100, blank=True, null=True)
    significant = models.BooleanField(default=False, help_text="Indique si cette maintenance est marquante")

    def is_due_soon(self):
        if self.completed_date:
            return False
        return self.scheduled_date <= timezone.now() + timezone.timedelta(days=7)

    def __str__(self):
        return f"{self.maintenance_type.name} - {self.machine.name}"
