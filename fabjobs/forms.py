from django import forms
from .models import Job, Material, JobFile
from fabmaintenance.models import Machine, MachineType
from datetime import timedelta
import re
import logging

logger = logging.getLogger(__name__)

class MaterialForm(forms.ModelForm):
    """Formulaire pour créer/modifier un matériau"""
    all_fablabs = forms.BooleanField(
        required=False,
        label="Ajouter à tous les FabLabs",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        initial=True  # Activé par défaut
    )

    class Meta:
        model = Material
        fields = ['name', 'description', 'unit', 'price_per_unit', 'co2_per_unit', 'color', 'machine_types', 'fablabs']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'unit': forms.Select(attrs={'class': 'form-control'}),
            'price_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'co2_per_unit': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'color': forms.HiddenInput(),
            'machine_types': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'fablabs': forms.SelectMultiple(attrs={'class': 'form-control'}),
        }

    def clean_color(self):
        color = self.cleaned_data.get('color', '#808080')
        # Vérifier si la couleur est un code hexadécimal valide
        if not re.match(r'^#[0-9A-Fa-f]{6}$', color):
            raise forms.ValidationError("La couleur doit être un code hexadécimal valide (ex: #FF0000)")
        return color.upper()  # Convertir en majuscules pour la cohérence

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les FabLabs en fonction des permissions de l'utilisateur
        if not user.is_superuser:
            self.fields['fablabs'].queryset = user.fablabs.all()
            if user.fablabs.count() == 1:
                self.fields['fablabs'].initial = user.fablabs.first()
                self.fields['fablabs'].widget.attrs['disabled'] = True
                self.fields['all_fablabs'].widget.attrs['disabled'] = True
        else:
            self.fields['fablabs'].queryset = user.fablabs.all()

        # Rendre le champ fablabs non requis
        self.fields['fablabs'].required = False

        # Désactiver la sélection des FabLabs si "Tous" est coché
        if self.initial.get('all_fablabs', True):
            self.fields['fablabs'].widget.attrs['disabled'] = True

    def clean(self):
        cleaned_data = super().clean()
        all_fablabs = cleaned_data.get('all_fablabs')
        fablabs = cleaned_data.get('fablabs')

        if all_fablabs:
            # Si "Tous" est coché, on utilise tous les FabLabs disponibles
            cleaned_data['fablabs'] = list(self.fields['fablabs'].queryset)
        elif not fablabs:
            # Si aucun FabLab n'est sélectionné et "Tous" n'est pas coché
            raise forms.ValidationError("Veuillez sélectionner au moins un FabLab ou cocher 'Ajouter à tous les FabLabs'.")

        return cleaned_data

class JobForm(forms.ModelForm):
    """Formulaire pour créer/modifier un job"""
    estimated_duration_hours = forms.IntegerField(
        min_value=0,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Heures'})
    )
    estimated_duration_minutes = forms.IntegerField(
        min_value=0,
        max_value=59,
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Minutes'})
    )

    class Meta:
        model = Job
        fields = ['name', 'description', 'machine', 'material', 'quantity', 'status', 
                 'assigned_to', 'notes']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'machine': forms.Select(attrs={'class': 'form-control'}),
            'material': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'assigned_to': forms.Select(attrs={'class': 'form-control select2-user'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrer les machines en fonction des FabLabs de l'utilisateur
        self.fields['machine'].queryset = Machine.objects.filter(
            fablab__in=user.fablabs.all()
        ).order_by('name')
        
        # Initialiser le queryset des matériaux
        if self.instance and self.instance.pk:
            self.fields['material'].queryset = Material.objects.filter(
                machine_types=self.instance.machine.machine_type,
                fablabs__in=user.fablabs.all()
            ).distinct().order_by('name')
        else:
            # Pour un nouveau job, on commence avec un queryset vide
            self.fields['material'].queryset = Material.objects.none()
        
        # Filtrer les utilisateurs assignables et ajouter leurs couleurs d'avatar
        users = user.fablabs.first().users.all()
        self.fields['assigned_to'].queryset = users
        
        # Modifier le label des options pour afficher le nom complet
        self.fields['assigned_to'].label_from_instance = lambda obj: obj.get_full_name() or obj.username

        # Définir la quantité par défaut à 1
        self.fields['quantity'].initial = 1

        # Rendre le champ description optionnel
        self.fields['description'].required = False

    def clean(self):
        cleaned_data = super().clean()
        
        # Si un matériau est sélectionné, s'assurer qu'il est dans les choix valides
        material = cleaned_data.get('material')
        if material:
            # Mettre à jour le queryset pour inclure le matériau sélectionné
            self.fields['material'].queryset = Material.objects.filter(
                id=material.id
            )
        
        hours = cleaned_data.get('estimated_duration_hours', 0) or 0
        minutes = cleaned_data.get('estimated_duration_minutes', 0) or 0
        
        if hours or minutes:
            cleaned_data['estimated_duration'] = timedelta(hours=hours, minutes=minutes)
        
        return cleaned_data

class JobFileForm(forms.ModelForm):
    """Formulaire pour ajouter un fichier à un job"""
    class Meta:
        model = JobFile
        fields = ['file', 'file_type', 'description']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control'}),
            'file_type': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        } 