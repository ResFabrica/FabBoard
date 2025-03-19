from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Machine, Maintenance, MaintenanceType, FabLab
from django.utils import timezone
import random

class MachineForm(forms.ModelForm):
    machine_type = forms.ChoiceField(
        label='Type de machine',
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'onchange': 'handleMachineTypeChange(this)'
        })
    )

    new_machine_type = forms.CharField(
        label='Nouveau type de machine',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le nom du nouveau type de machine'
        })
    )

    class Meta:
        model = Machine
        fields = ['name', 'machine_type', 'new_machine_type', 'fablab', 'serial_number', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'fablab': forms.Select(attrs={'class': 'form-control'}),
            'serial_number': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter l'option "Autre..." dans les choix de type de machine
        from .models import MachineType
        choices = [(None, '---------')]
        choices.extend([(str(mt.id), str(mt)) for mt in MachineType.objects.all()])
        choices.append(('new', 'Autre...'))
        self.fields['machine_type'].choices = choices

        # Toujours filtrer les FabLabs par ceux de l'utilisateur
        if user:
            self.fields['fablab'].queryset = user.fablabs.all()
            # Toujours sélectionner le premier FabLab par défaut
            if user.fablabs.exists():
                self.fields['fablab'].initial = user.fablabs.first()
                # Si l'utilisateur n'a qu'un seul FabLab, rendre le champ en lecture seule
                if user.fablabs.count() == 1:
                    self.fields['fablab'].widget.attrs['readonly'] = True
        else:
            # Définir le premier fablab comme valeur par défaut
            from .models import FabLab
            first_fablab = FabLab.objects.first()
            if first_fablab:
                self.fields['fablab'].initial = first_fablab

    def clean(self):
        cleaned_data = super().clean()
        machine_type = cleaned_data.get('machine_type')
        new_machine_type = cleaned_data.get('new_machine_type')

        if machine_type == 'new':
            if not new_machine_type:
                self.add_error('new_machine_type', 'Ce champ est requis pour un nouveau type de machine')
            else:
                # Créer le nouveau type de machine
                from .models import MachineType
                machine_type_obj, created = MachineType.objects.get_or_create(
                    name=new_machine_type,
                    defaults={'description': f'Type de machine créé le {timezone.now().strftime("%d/%m/%Y")}'}
                )
                cleaned_data['machine_type'] = machine_type_obj
        else:
            # Convertir l'ID en objet MachineType
            from .models import MachineType
            try:
                cleaned_data['machine_type'] = MachineType.objects.get(pk=int(machine_type))
            except (ValueError, MachineType.DoesNotExist):
                self.add_error('machine_type', 'Type de machine invalide')

        return cleaned_data

class MaintenanceForm(forms.ModelForm):
    maintenance_type_choice = forms.ChoiceField(
        label='Type de maintenance',
        choices=[],  # Sera rempli dans __init__
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    custom_type_name = forms.CharField(
        label='Type de maintenance personnalisé',
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Entrez le type de maintenance'
        })
    )

    scheduling_type = forms.ChoiceField(
        label='Type de programmation',
        choices=Maintenance.SCHEDULING_TYPES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        initial='today'
    )
    
    scheduled_date = forms.DateField(
        label='Date prévue',
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    period_days = forms.IntegerField(
        label='Période (en jours)',
        required=False,
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = Maintenance
        fields = ['maintenance_type_choice', 'custom_type_name', 'scheduling_type', 'scheduled_date', 'period_days', 'notes', 'significant']
        widgets = {
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'significant': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, machine=None, *args, **kwargs):
        self.machine = machine  # Sauvegarder la machine pour l'utiliser plus tard
        super().__init__(*args, **kwargs)
        if machine:
            # Ajouter l'option "Autre" à la fin de la liste des types de maintenance
            maintenance_types = MaintenanceType.objects.filter(
                machine_type=machine.machine_type,
                is_custom=False
            )
            choices = [(str(mt.id), str(mt)) for mt in maintenance_types]
            choices.append(('other', 'Autre...'))
            self.fields['maintenance_type_choice'].choices = choices
            
            # Suggérer la période par défaut du type de maintenance
            self.fields['period_days'].help_text = "Suggestion : utiliser la fréquence recommandée du type de maintenance"

            # Configurer le champ significant
            self.fields['significant'].label = "Maintenance marquante"
            self.fields['significant'].help_text = "Cochez cette case si cette maintenance est particulièrement importante"

        # Ajouter du JavaScript pour gérer l'affichage du champ personnalisé
        self.fields['maintenance_type_choice'].widget.attrs['onchange'] = 'handleMaintenanceTypeChange(this)'

        # Supprimer le champ maintenance_type du formulaire car nous utilisons maintenance_type_choice à la place
        if 'maintenance_type' in self.fields:
            del self.fields['maintenance_type']

    def clean(self):
        cleaned_data = super().clean()
        maintenance_type_choice = cleaned_data.get('maintenance_type_choice')
        custom_type_name = cleaned_data.get('custom_type_name')
        scheduling_type = cleaned_data.get('scheduling_type')
        scheduled_date = cleaned_data.get('scheduled_date')
        period_days = cleaned_data.get('period_days')

        if maintenance_type_choice == 'other' and not custom_type_name:
            self.add_error('custom_type_name', 'Ce champ est requis pour un type personnalisé')

        if scheduling_type == 'scheduled' and not scheduled_date:
            self.add_error('scheduled_date', 'La date est requise pour une maintenance planifiée')
        
        if scheduling_type == 'periodic' and not period_days:
            self.add_error('period_days', 'La période est requise pour une maintenance périodique')

        now = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)

        # Convertir la date en datetime
        if scheduling_type == 'scheduled' and scheduled_date:
            cleaned_data['scheduled_date'] = timezone.make_aware(
                timezone.datetime.combine(scheduled_date, timezone.datetime.min.time().replace(hour=12))
            )
        elif scheduling_type == 'today':
            cleaned_data['scheduled_date'] = now
            cleaned_data['completed_date'] = now  # Marquer comme complétée automatiquement
        elif scheduling_type == 'periodic':
            cleaned_data['scheduled_date'] = now

        return cleaned_data

    def save(self, commit=True):
        maintenance = super().save(commit=False)
        maintenance.machine = self.machine  # Définir la machine
        maintenance_type_choice = self.cleaned_data['maintenance_type_choice']
        scheduling_type = self.cleaned_data['scheduling_type']
        
        # Si c'est un type personnalisé, créer un nouveau type de maintenance
        if maintenance_type_choice == 'other':
            # Définir period_days selon le type de programmation
            if scheduling_type == 'periodic':
                period_days = self.cleaned_data.get('period_days')
            else:
                # Pour les maintenances non périodiques, utiliser une valeur par défaut
                period_days = 30

            maintenance_type = MaintenanceType.objects.create(
                name=self.cleaned_data['custom_type_name'],
                description=f"Type de maintenance personnalisé créé le {timezone.now().strftime('%d/%m/%Y')}",
                machine_type=self.machine.machine_type,
                is_custom=True,
                period_days=period_days
            )
            maintenance.maintenance_type = maintenance_type
            maintenance.custom_type_name = self.cleaned_data['custom_type_name']
        else:
            # Sinon, utiliser le type de maintenance existant
            maintenance.maintenance_type = MaintenanceType.objects.get(pk=int(maintenance_type_choice))
        
        if commit:
            maintenance.save()
        return maintenance

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(
        label='Prénom',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        label='Nom',
        max_length=30,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    fablab_name = forms.CharField(
        label='Nom du FabLab',
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    accept_terms = forms.BooleanField(
        label='J\'accepte les conditions générales d\'utilisation',
        required=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    accept_contact = forms.BooleanField(
        label='J\'accepte d\'être contacté par Res Fabrica',
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    captcha_answer = forms.IntegerField(
        label='Vérification humaine',
        required=True,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    captcha_label = forms.CharField(required=False, widget=forms.HiddenInput())

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'password1', 'password2', 'fablab_name', 'accept_terms', 'accept_contact', 'captcha_answer')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        
        # Utiliser le label du CAPTCHA s'il est fourni dans initial
        if 'initial' in kwargs and 'captcha_label' in kwargs['initial']:
            self.fields['captcha_answer'].label = kwargs['initial']['captcha_label']

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Cette adresse email est déjà utilisée.')
        return email

    def clean_fablab_name(self):
        fablab_name = self.cleaned_data.get('fablab_name')
        if FabLab.objects.filter(name__iexact=fablab_name).exists():
            raise forms.ValidationError('Un FabLab avec ce nom existe déjà.')
        return fablab_name

    def clean_captcha_answer(self):
        answer = self.cleaned_data.get('captcha_answer')
        request = self.request if hasattr(self, 'request') else None
        if request and 'captcha_num1' in request.session and 'captcha_num2' in request.session:
            expected = request.session['captcha_num1'] + request.session['captcha_num2']
            if answer != expected:
                raise forms.ValidationError('La réponse est incorrecte. Veuillez réessayer.')
        else:
            raise forms.ValidationError('Session CAPTCHA expirée. Veuillez recharger la page.')
        return answer

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Utiliser l'email comme nom d'utilisateur
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user