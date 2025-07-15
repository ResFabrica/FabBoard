from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from fabmaintenance.models import Machine, MachineType
from fabusers.models import FabLab
from decimal import Decimal

class Material(models.Model):
    """Matériaux utilisables pour les jobs"""
    UNIT_CHOICES = [
        ('g', 'Grammes'),
        ('kg', 'Kilogrammes'),
        ('m', 'Mètres'),
        ('cm', 'Centimètres'),
        ('mm', 'Millimètres'),
        ('l', 'Litres'),
        ('ml', 'Millilitres'),
        ('pcs', 'Pièces'),
    ]

    COLOR_CHOICES = [
        '#FF0000',
        '#FF4500',
        '#FFA500',
        '#FFD700',
        '#FFFF00',
        '#9ACD32',
        '#32CD32',
        '#008000',
        '#20B2AA',
        '#00FFFF',
        '#1E90FF',
        '#0000FF',
        '#4B0082',
        '#8A2BE2',
        '#9400D3',
        '#FF1493',
        '#FF69B4',
        '#FFB6C1',
        '#FFC0CB',
        '#FFE4E1',
        '#A52A2A',
        '#8B4513',
        '#D2691E',
        '#CD853F',
        '#DEB887',
        '#F5F5DC',
        '#FAEBD7',
        '#FFFAF0',
        '#F0F8FF',
        '#F5F5F5',
        '#E6E6FA',
        '#FFF0F5',
        '#FFE4B5',
        '#FFDAB9',
        '#E0FFFF',
        '#F0FFFF',
        '#F0FFF0',
        '#FFF0F5',
        '#FFE4E1',
        '#E6E6FA',
        '#D8BFD8',
        '#DDA0DD',
        '#EE82EE',
        '#FF00FF',
        '#BA55D3',
        '#9370DB',
        '#8A2BE2',
        '#9400D3',
        '#9932CC',
        '#8B008B',
    ]

    name = models.CharField(max_length=100, verbose_name="Nom", unique=True)
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    unit = models.CharField(max_length=3, choices=UNIT_CHOICES, verbose_name="Unité")
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix par unité")
    co2_per_unit = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="CO2 par unité (kg)")
    color = models.CharField(max_length=7, default="#808080", verbose_name="Couleur")
    machine_types = models.ManyToManyField(MachineType, verbose_name="Types de machines compatibles")
    fablabs = models.ManyToManyField(FabLab, verbose_name="FabLabs")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Matériau"
        verbose_name_plural = "Matériaux"
        ordering = ['name']

class Job(models.Model):
    """Job de fabrication (impression 3D, découpe laser, etc.)"""
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('in_progress', 'En cours'),
        ('completed', 'Terminé'),
        ('cancelled', 'Annulé'),
        ('failed', 'Échoué'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    machine = models.ForeignKey(Machine, on_delete=models.CASCADE, verbose_name="Machine")
    material = models.ForeignKey(Material, on_delete=models.CASCADE, verbose_name="Matériau")
    quantity = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Quantité")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_jobs', verbose_name="Créé par")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_jobs', verbose_name="Assigné à")
    start_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de début")
    end_date = models.DateTimeField(null=True, blank=True, verbose_name="Date de fin")
    estimated_duration = models.DurationField(null=True, blank=True, verbose_name="Durée estimée")
    actual_duration = models.DurationField(null=True, blank=True, verbose_name="Durée réelle")
    material_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût matière")
    energy_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût énergie")
    total_cost = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Coût total")
    co2_emission = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, verbose_name="Émission CO2 (kg)")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")
    updated_at = models.DateTimeField(default=timezone.now, verbose_name="Mis à jour le")

    def calculate_costs(self):
        """Calcule les coûts et émissions CO2 du job"""
        if self.material and self.quantity:
            # Coût matière
            self.material_cost = self.material.price_per_unit * self.quantity
            
            # Émission CO2 matière
            material_co2 = self.material.co2_per_unit * self.quantity
            
            # Coût énergie (à adapter selon le type de machine)
            energy_cost_per_hour = Decimal('0.15')  # Exemple: 0.15€/kWh
            if self.actual_duration:
                hours = self.actual_duration.total_seconds() / 3600
                self.energy_cost = Decimal(str(hours)) * energy_cost_per_hour
                
                # Émission CO2 énergie (exemple: 0.1kg CO2/kWh)
                energy_co2 = Decimal(str(hours)) * Decimal('0.1')
                self.co2_emission = material_co2 + energy_co2
            
            # Coût total
            self.total_cost = self.material_cost + (self.energy_cost or Decimal('0'))
            
            self.save()

    def __str__(self):
        return f"{self.name} - {self.machine.name}"

    class Meta:
        verbose_name = "Job"
        verbose_name_plural = "Jobs"
        ordering = ['-created_at']

class JobFile(models.Model):
    """Fichiers associés à un job (STL, GCODE, etc.)"""
    FILE_TYPES = [
        ('design', 'Fichier de conception'),
        ('gcode', 'GCODE'),
        ('result', 'Résultat'),
        ('other', 'Autre'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='files', verbose_name="Job")
    file = models.FileField(upload_to='job_files/', verbose_name="Fichier")
    file_type = models.CharField(max_length=20, choices=FILE_TYPES, verbose_name="Type de fichier")
    description = models.CharField(max_length=255, blank=True, null=True, verbose_name="Description")
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Uploadé par")
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Créé le")

    def __str__(self):
        return f"{self.get_file_type_display()} - {self.job.name}"

    class Meta:
        verbose_name = "Fichier de job"
        verbose_name_plural = "Fichiers de jobs"
        ordering = ['-created_at'] 