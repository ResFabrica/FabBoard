from django import forms
from django.contrib.auth import get_user_model
from .models import View, Section, Task, SubTask, Tag, CustomField, FabLab, CustomFieldValue, TaskFile
from django.utils.html import format_html
from django.forms.widgets import FILE_INPUT_CONTRADICTION, Input
import logging
import datetime

logger = logging.getLogger(__name__)

class TagWidget(forms.TextInput):
    """Widget personnalisé pour la gestion des tags avec Select2."""
    template_name = 'fabprojects/widgets/tag_widget.html'

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        if value:
            # Convertir la valeur en liste de tags si ce n'est pas déjà le cas
            if not isinstance(value, (list, tuple)):
                value = [v.strip() for v in value.split(',') if v.strip()]
            # Récupérer les tags existants
            tags = Tag.objects.filter(id__in=value)
            # Mettre à jour le contexte avec les tags et la valeur
            context['widget']['tags'] = [{'id': tag.id, 'text': tag.name, 'color': tag.color} for tag in tags]
            context['widget']['value'] = ','.join(str(tag.id) for tag in tags)
        return context

class ViewForm(forms.ModelForm):
    class Meta:
        model = View
        fields = ['name', 'fablab', 'custom_fields']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'fablab': forms.Select(attrs={'class': 'form-control'}),
            'custom_fields': forms.SelectMultiple(attrs={'class': 'form-control select2'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filtrer les FabLabs de l'utilisateur
            user_fablabs = user.fablabs.all()
            self.fields['fablab'].queryset = user_fablabs
            
            # Filtrer les champs personnalisés du FabLab
            if self.instance.pk:
                self.fields['custom_fields'].queryset = CustomField.objects.filter(fablab=self.instance.fablab)
            elif user_fablabs.exists():
                # Pour un nouveau formulaire, présélectionner le premier FabLab
                first_fablab = user_fablabs.first()
                self.initial['fablab'] = first_fablab
                self.fields['custom_fields'].queryset = CustomField.objects.filter(fablab=first_fablab)
            else:
                self.fields['custom_fields'].queryset = CustomField.objects.none()

    def clean(self):
        cleaned_data = super().clean()
        fablab = cleaned_data.get('fablab')
        custom_fields = cleaned_data.get('custom_fields')

        # Vérifier que les champs personnalisés appartiennent au bon FabLab
        if fablab and custom_fields:
            invalid_fields = [field for field in custom_fields if field.fablab != fablab]
            if invalid_fields:
                self.add_error('custom_fields', 
                    'Certains champs personnalisés n\'appartiennent pas au FabLab sélectionné.')

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'order']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'order': forms.NumberInput(attrs={'class': 'form-control'})
        }

class AjaxModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    def __init__(self, queryset, fablab=None, **kwargs):
        self.fablab = fablab
        super().__init__(queryset, **kwargs)

    def _set_fablab(self, fablab):
        self.fablab = fablab
        if fablab:
            self.queryset = self.queryset.model.objects.filter(fablab=fablab)

    def to_python(self, value):
        if not value:
            return []
        
        # Séparer les IDs existants des nouveaux tags
        ids = []
        new_tags = []
        
        for val in value:
            try:
                ids.append(int(val))
            except (ValueError, TypeError):
                if val and isinstance(val, str):
                    new_tags.append(val)
        
        # Retourner la liste des IDs et des nouveaux tags
        return ids + new_tags
    
    def clean(self, value):
        value = self.to_python(value)
        if not value:
            if self.required:
                raise forms.ValidationError(self.error_messages['required'])
            return []
        
        # Séparer les IDs existants des nouveaux tags
        ids = []
        new_tags = []
        for val in value:
            if isinstance(val, int):
                ids.append(val)
            else:
                new_tags.append(val)
        
        # Récupérer les tags existants
        existing_tags = Tag.objects.filter(id__in=ids)
        
        # Créer les nouveaux tags
        result_tags = list(existing_tags)
        for tag_name in new_tags:
            new_tag = Tag.objects.create(
                name=tag_name,
                fablab=self.fablab,
                color='#6c757d'  # Couleur par défaut
            )
            result_tags.append(new_tag)
        
        return result_tags

class MultipleFileInput(Input):
    input_type = 'file'
    needs_multipart_form = True
    
    def __init__(self, attrs=None):
        default_attrs = {'multiple': True}
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)

    def get_context(self, name, value, attrs):
        context = super().get_context(name, value, attrs)
        context['widget']['attrs'].update({
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.zip,.jpg,.jpeg,.png,.gif'
        })
        return context

    def value_from_datadict(self, data, files, name):
        if not files:
            return []
            
        if hasattr(files, 'getlist'):
            return files.getlist(name)
            
        return files.get(name)

class TagsModelMultipleChoiceField(forms.ModelMultipleChoiceField):
    """Champ personnalisé pour les tags qui affiche le nom plutôt que l'ID"""
    def label_from_instance(self, obj):
        return obj.name

class TaskForm(forms.ModelForm):
    """Formulaire pour créer/modifier une tâche."""
    tags = TagsModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control',
            'id': 'id_tags'
        }),
        help_text='Sélectionnez ou créez des tags pour catégoriser cette tâche'
    )
    
    class Meta:
        model = Task
        fields = ['title', 'description', 'deadline', 'assigned_users', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'data-editor': 'markdown',
                'rows': 10,
                'placeholder': 'Décrivez la tâche en utilisant Markdown...'
            }),
            'deadline': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'assigned_users': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        }
        labels = {
            'title': 'Titre',
            'description': 'Description',
            'deadline': 'Date limite',
            'assigned_users': 'Utilisateurs assignés',
            'tags': 'Tags'
        }
    
    def __init__(self, *args, section=None, fablab=None, **kwargs):
        self.section = section
        self.fablab = fablab or (section.view.fablab if section else None)
        
        # Vérifier si on a une instance existante
        instance = kwargs.get('instance')
        
        # Créer un dictionnaire initial pour tous les champs si pas déjà présent
        if instance and 'initial' not in kwargs:
            initial = {}
            
            # Préparer les tags
            tags_list = list(instance.tags.all().select_related('fablab'))
            initial['tags'] = [tag.id for tag in tags_list]
            
            # Préparer les utilisateurs assignés
            users_list = list(instance.assigned_users.all())
            initial['assigned_users'] = [user.id for user in users_list]
            
            # Formater la date limite si elle existe
            if instance.deadline:
                if isinstance(instance.deadline, datetime.datetime):
                    initial['deadline'] = instance.deadline.strftime('%Y-%m-%d')
            
            # Ajouter les champs de base
            initial['title'] = instance.title
            initial['description'] = instance.description
            
            # Définir les valeurs initiales pour le formulaire
            kwargs['initial'] = initial
        
        super().__init__(*args, **kwargs)
        
        # S'assurer que le queryset des tags est correctement filtré par FabLab
        if self.fablab:
            self.fields['tags'].queryset = Tag.objects.filter(fablab=self.fablab)
            self.fields['assigned_users'].queryset = self.fablab.users.all()
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Pour les tags créés via Select2 "tags: true", créer de nouveaux objets Tag
        if 'tags' in self.data:
            # Si des nouveaux tags ont été créés (valeurs qui ne sont pas des IDs)
            new_tag_names = [tag for tag in self.data.getlist('tags') if not tag.isdigit()]
            
            # Créer les nouveaux tags et les ajouter à cleaned_data['tags']
            for tag_name in new_tag_names:
                tag, created = Tag.objects.get_or_create(
                    name=tag_name,
                    fablab=self.fablab,
                    defaults={'name': tag_name}
                )
                
                if 'tags' in cleaned_data:
                    if not isinstance(cleaned_data['tags'], list):
                        cleaned_data['tags'] = list(cleaned_data['tags'])
                    if tag not in cleaned_data['tags']:
                        cleaned_data['tags'].append(tag)
        
        return cleaned_data
    
    def save(self, commit=True):
        task = super().save(commit=False)
        if self.section:
            task.section = self.section
        if commit:
            task.save()
            if 'tags' in self.cleaned_data:
                self.save_m2m()  # Sauvegarde des relations many-to-many, y compris les tags
        
        return task

class SubTaskForm(forms.ModelForm):
    class Meta:
        model = SubTask
        fields = ['title']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'})
        }

class TagForm(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'form-control form-control-color'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_name(self):
        name = self.cleaned_data['name']
        if self.user:
            # Vérifier si un tag avec ce nom existe déjà dans l'un des FabLabs de l'utilisateur
            existing_tag = Tag.objects.filter(
                name__iexact=name,  # iexact pour une comparaison insensible à la casse
                fablab__in=self.user.fablabs.all()
            ).first()
            
            if existing_tag:
                if not self.instance.pk or self.instance.pk != existing_tag.pk:
                    raise forms.ValidationError(
                        f"Un tag nommé '{name}' existe déjà dans l'un de vos FabLabs."
                    )
        return name

    def save(self, commit=True):
        tag = super().save(commit=False)
        if commit and self.user:
            # Si c'est un nouveau tag
            if not tag.pk:
                # Créer le tag pour chaque FabLab de l'utilisateur
                tags = []
                for fablab in self.user.fablabs.all():
                    new_tag = Tag(
                        name=tag.name,
                        color=tag.color,
                        fablab=fablab
                    )
                    new_tag.save()
                    tags.append(new_tag)
                return tags[0] if tags else None
            else:
                # Si c'est une modification, mettre à jour tous les tags avec le même nom
                Tag.objects.filter(
                    name=tag.name,
                    fablab__in=self.user.fablabs.all()
                ).update(
                    name=self.cleaned_data['name'],
                    color=self.cleaned_data['color']
                )
                tag.refresh_from_db()
                return tag
        return tag

class CustomFieldForm(forms.ModelForm):
    class Meta:
        model = CustomField
        fields = ['name', 'field_type', 'choices', 'fablab']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'field_type': forms.Select(attrs={'class': 'form-control'}),
            'choices': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'fablab': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user:
            # Filtrer les FabLabs de l'utilisateur
            user_fablabs = user.fablabs.all()
            self.fields['fablab'].queryset = user_fablabs
            
            # Si c'est un nouveau formulaire (pas d'instance) et qu'il y a au moins un FabLab
            if not self.instance.pk and user_fablabs.exists():
                # Présélectionner le premier FabLab
                self.initial['fablab'] = user_fablabs.first()

    def clean(self):
        cleaned_data = super().clean()
        field_type = cleaned_data.get('field_type')
        choices = cleaned_data.get('choices')

        if field_type == 'choice' and not choices:
            raise forms.ValidationError({
                'choices': "Les options sont requises pour un champ de type 'choix'."
            }) 