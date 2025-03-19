from django import forms
from django.contrib.auth import get_user_model
from .models import View, Section, Task, SubTask, Tag, CustomField, FabLab, CustomFieldValue, TaskFile
from django.utils.html import format_html
from django.forms.widgets import FILE_INPUT_CONTRADICTION, Input
import logging

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
        logger.info("\n=== MultipleFileInput.__init__ ===")
        default_attrs = {'multiple': True}
        if attrs:
            logger.info(f"Attrs fournis: {attrs}")
            default_attrs.update(attrs)
        logger.info(f"Attrs finaux: {default_attrs}")
        super().__init__(default_attrs)

    def get_context(self, name, value, attrs):
        logger.info("\n=== MultipleFileInput.get_context ===")
        logger.info(f"Name: {name}")
        logger.info(f"Value: {value}")
        logger.info(f"Attrs avant: {attrs}")
        
        context = super().get_context(name, value, attrs)
        context['widget']['attrs'].update({
            'class': 'form-control',
            'accept': '.pdf,.doc,.docx,.xls,.xlsx,.zip,.jpg,.jpeg,.png,.gif'
        })
        logger.info(f"Context final: {context}")
        return context

    def value_from_datadict(self, data, files, name):
        logger.info("\n=== MultipleFileInput.value_from_datadict ===")
        logger.info(f"Name: {name}")
        logger.info(f"Data keys: {data.keys() if data else 'None'}")
        logger.info(f"Files keys: {files.keys() if files else 'None'}")
        logger.info(f"Files type: {type(files)}")
        
        if not files:
            logger.info("Pas de fichiers dans la requête")
            return []
            
        if hasattr(files, 'getlist'):
            files_list = files.getlist(name)
            logger.info(f"Files list from getlist: {files_list}")
            return files_list
            
        file = files.get(name)
        logger.info(f"Single file from get: {file}")
        return file

class TaskForm(forms.ModelForm):
    deadline = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'form-control'
        })
    )

    tags = AjaxModelMultipleChoiceField(
        queryset=Tag.objects.none(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )

    files = forms.Field(
        widget=MultipleFileInput(),
        required=False,
        label='Fichiers',
        help_text='Sélectionnez un ou plusieurs fichiers'
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'assigned_users', 'deadline', 'tags']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'assigned_users': forms.SelectMultiple(attrs={'class': 'form-control select2'}),
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'tags': forms.SelectMultiple(attrs={'class': 'form-control select2'})
        }
        labels = {
            'assigned_users': 'Utilisateurs assignés',
        }

    def __init__(self, *args, **kwargs):
        section = kwargs.pop('section', None)
        super().__init__(*args, **kwargs)
        self.section = section
        
        if section:
            self.fields['assigned_users'].queryset = section.view.fablab.users.all()
            self.fields['tags'].queryset = Tag.objects.filter(fablab=section.view.fablab)
            
            # Initialiser les utilisateurs avec leur nom complet
            if self.instance.pk:
                self.fields['assigned_users'].initial = self.instance.assigned_users.all()
                self.fields['assigned_users'].widget.choices = [
                    (user.id, user.get_full_name() or user.username)
                    for user in section.view.fablab.users.all()
                ]
            
            # Initialiser les tags avec leurs IDs
            if self.instance.pk:
                self.initial['tags'] = [tag.id for tag in self.instance.tags.all()]
                
            # Ajouter les champs personnalisés
            for custom_field in section.view.custom_fields.all():
                field_name = f'custom_field_{custom_field.id}'
                field_value = None
                
                if self.instance.pk:
                    try:
                        field_value = self.instance.custom_field_values.get(field=custom_field).value
                    except CustomFieldValue.DoesNotExist:
                        pass
                
                if custom_field.field_type == 'boolean':
                    self.fields[field_name] = forms.BooleanField(
                        required=False,
                        initial=field_value == 'true' if field_value is not None else False,
                        label=custom_field.name
                    )
                elif custom_field.field_type == 'number':
                    self.fields[field_name] = forms.FloatField(
                        required=False,
                        initial=field_value,
                        label=custom_field.name
                    )
                elif custom_field.field_type == 'date':
                    self.fields[field_name] = forms.DateField(
                        required=False,
                        initial=field_value,
                        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
                        label=custom_field.name
                    )
                elif custom_field.field_type == 'choice':
                    choices = [(c.strip(), c.strip()) for c in custom_field.choices.split('\n') if c.strip()]
                    choices.insert(0, ('', '---------'))
                    self.fields[field_name] = forms.ChoiceField(
                        choices=choices,
                        required=False,
                        initial=field_value,
                        label=custom_field.name
                    )
                else:  # text
                    self.fields[field_name] = forms.CharField(
                        required=False,
                        initial=field_value,
                        label=custom_field.name
                    )

    def clean_files(self):
        logger.info("\n=== TaskForm.clean_files ===")
        files = self.files.getlist('files') if self.files else []
        logger.info(f"Files from request: {files}")
        logger.info(f"Files type: {type(files)}")
        logger.info(f"Number of files: {len(files)}")
        
        if not files:
            logger.info("Aucun fichier trouvé")
            return []
            
        for file in files:
            logger.info(f"File details - Name: {file.name}, Size: {file.size}, Type: {file.content_type}")
            logger.info(f"File object type: {type(file)}")
            logger.info(f"File object attributes: {dir(file)}")
        
        return files

    def clean(self):
        logger.info("\n=== TaskForm.clean ===")
        cleaned_data = super().clean()
        logger.info(f"Initial cleaned data: {cleaned_data}")
        
        # Récupérer les fichiers depuis clean_files
        if 'files' not in cleaned_data:
            cleaned_data['files'] = self.clean_files()
            logger.info(f"Files ajoutés à cleaned_data: {cleaned_data['files']}")
        
        logger.info(f"Final cleaned data: {cleaned_data}")
        return cleaned_data

    def save(self, commit=True):
        task = super().save(commit=False)
        if self.section:
            task.section = self.section
            task.view = self.section.view
        
        if commit:
            task.save()
            # Gérer les relations many-to-many
            self.save_m2m()
            
            # Sauvegarder les fichiers
            files = self.cleaned_data.get('files', [])
            for file in files:
                if file:
                    TaskFile.objects.create(
                        task=task,
                        file=file,
                        filename=file.name,
                        file_type=file.content_type,
                        file_size=file.size
                    )
            
            # Sauvegarder les valeurs des champs personnalisés
            for field_name, value in self.cleaned_data.items():
                if field_name.startswith('custom_field_'):
                    field_id = int(field_name.split('_')[-1])
                    custom_field = CustomField.objects.get(id=field_id)
                    CustomFieldValue.objects.update_or_create(
                        task=task,
                        field=custom_field,
                        defaults={'value': str(value) if value is not None else ''}
                    )
        
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