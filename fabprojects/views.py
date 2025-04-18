from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import View, Section, Task, SubTask, Tag, CustomField, CustomFieldValue, TaskFile
from fabmaintenance.models import FabLab
from .forms import ViewForm, SectionForm, TaskForm, SubTaskForm, TagForm, CustomFieldForm
import json
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.contrib.auth.models import User
from django.db import transaction
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@login_required
def project_home(request):
    """Page d'accueil des projets."""
    # Toujours filtrer par les FabLabs de l'utilisateur, même pour les administrateurs
    user_fablabs = request.user.fablabs.all()
    views = View.objects.filter(fablab__in=user_fablabs)
    
    # Récupérer les tâches assignées à l'utilisateur
    tasks = Task.objects.filter(
        assigned_users=request.user,
        is_completed=False
    ).select_related('section__view').order_by('deadline')
    
    # Enrichir les FabLabs avec les compteurs
    for fablab in user_fablabs:
        # Compter les tâches en cours
        fablab.task_count = Task.objects.filter(
            section__view__fablab=fablab,
            is_completed=False
        ).count()
        
        # Compter les vues
        fablab.view_count = View.objects.filter(fablab=fablab).count()
    
    context = {
        'views': views,
        'user_fablabs': user_fablabs,
        'tasks': tasks,
        'now': timezone.now().date(),
    }
    return render(request, 'fabprojects/home.html', context)

@login_required
def view_list(request):
    """Liste des vues de projets."""
    user_fablabs = request.user.fablabs.all()
    views = View.objects.filter(fablab__in=user_fablabs)
    context = {
        'views': views,
    }
    return render(request, 'fabprojects/view_list.html', context)

@login_required
def view_detail(request, view_id):
    """Détail d'une vue avec ses sections et tâches."""
    view = get_object_or_404(View, id=view_id)
    if not view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    sections = view.sections.all().prefetch_related(
        'tasks__assigned_users',
        'tasks__tags',
    ).order_by('order')
    
    # Récupérer les tags de tous les FabLabs de l'utilisateur
    user_fablabs = request.user.fablabs.all()
    available_tags = Tag.objects.filter(fablab__in=user_fablabs).distinct()
    
    context = {
        'view': view,
        'sections': sections,
        'now': timezone.now().date(),
        'available_tags': available_tags,
        'users': view.fablab.users.all(),
    }
    return render(request, 'fabprojects/view_detail.html', context)

@login_required
def my_tasks(request):
    """Vue des tâches assignées à l'utilisateur."""
    tasks = Task.objects.filter(
        assigned_users=request.user,
        is_completed=False
    ).select_related('section__view').order_by('deadline')
    
    # Récupérer les tags disponibles de tous les FabLabs de l'utilisateur
    user_fablabs = request.user.fablabs.all()
    available_tags = Tag.objects.filter(fablab__in=user_fablabs)
    
    context = {
        'tasks': tasks,
        'available_tags': available_tags,
        'now': timezone.now().date(),
    }
    return render(request, 'fabprojects/my_tasks.html', context)

@login_required
def fablab_tasks(request):
    """Vue de toutes les tâches du FabLab."""
    user_fablabs = request.user.fablabs.all()
    
    # Récupérer les tâches avec toutes les relations nécessaires
    tasks = Task.objects.filter(
        section__view__fablab__in=user_fablabs
    ).select_related(
        'section__view__fablab'
    ).prefetch_related(
        'assigned_users',
        'tags'
    ).order_by(
        'section__view__fablab__name',
        'deadline'
    )
    
    # Organiser les tâches par FabLab
    fablab_tasks = {}
    for task in tasks:
        fablab_id = task.section.view.fablab.id
        if fablab_id not in fablab_tasks:
            fablab_tasks[fablab_id] = {
                'fablab': task.section.view.fablab,
                'tasks': []
            }
        fablab_tasks[fablab_id]['tasks'].append(task)
    
    # Récupérer les tags disponibles
    available_tags = Tag.objects.filter(fablab__in=user_fablabs)
    
    context = {
        'fablab_tasks': fablab_tasks.values(),
        'available_tags': available_tags,
        'now': timezone.now().date(),
    }
    return render(request, 'fabprojects/fablab_tasks.html', context)

@login_required
def task_toggle_complete(request, task_id):
    """Basculer l'état de complétion d'une tâche."""
    task = get_object_or_404(Task, id=task_id)
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    task.is_completed = not task.is_completed
    task.save()
    
    return JsonResponse({
        'status': 'success',
        'is_completed': task.is_completed
    })

@login_required
def view_create(request):
    """Créer une nouvelle vue."""
    if request.method == 'POST':
        form = ViewForm(request.POST, user=request.user)
        if form.is_valid():
            view = form.save()
            messages.success(request, 'Vue créée avec succès.')
            return redirect('fabprojects:view_detail', view_id=view.id)
    else:
        form = ViewForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Nouvelle Vue'
    }
    return render(request, 'fabprojects/view_form.html', context)

@login_required
def view_edit(request, view_id):
    """Modifier une vue existante."""
    view = get_object_or_404(View, id=view_id)
    if not view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = ViewForm(request.POST, instance=view, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vue modifiée avec succès.')
            return redirect('fabprojects:view_detail', view_id=view.id)
    else:
        form = ViewForm(instance=view, user=request.user)
    
    context = {
        'form': form,
        'view': view,
        'title': 'Modifier la Vue'
    }
    return render(request, 'fabprojects/view_form.html', context)

@login_required
def view_delete(request, view_id):
    """Supprimer une vue."""
    view = get_object_or_404(View, id=view_id)
    if not view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        view.delete()
        messages.success(request, 'Vue supprimée avec succès.')
        return redirect('fabprojects:view_list')
    
    context = {
        'view': view,
    }
    return render(request, 'fabprojects/view_confirm_delete.html', context)

@login_required
def section_create(request, view_id):
    """Créer une nouvelle section dans une vue."""
    view = get_object_or_404(View, id=view_id)
    if not view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = SectionForm(request.POST)
        if form.is_valid():
            section = form.save(commit=False)
            section.view = view
            section.save()
            messages.success(request, 'Section créée avec succès.')
            return redirect('fabprojects:view_detail', view_id=view.id)
    else:
        form = SectionForm()
    
    context = {
        'form': form,
        'view': view,
        'title': 'Nouvelle Section'
    }
    return render(request, 'fabprojects/section_form.html', context)

@login_required
def section_edit(request, section_id):
    """Modifier une section existante."""
    section = get_object_or_404(Section, id=section_id)
    if not section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = SectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            messages.success(request, 'Section modifiée avec succès.')
            return redirect('fabprojects:view_detail', view_id=section.view.id)
    else:
        form = SectionForm(instance=section)
    
    context = {
        'form': form,
        'section': section,
        'title': 'Modifier la Section'
    }
    return render(request, 'fabprojects/section_form.html', context)

@login_required
def section_delete(request, section_id):
    """Supprimer une section."""
    section = get_object_or_404(Section, id=section_id)
    if not section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        view_id = section.view.id
        section.delete()
        messages.success(request, 'Section supprimée avec succès.')
        return redirect('fabprojects:view_detail', view_id=view_id)
    
    context = {
        'section': section,
    }
    return render(request, 'fabprojects/section_confirm_delete.html', context)

@login_required
def task_create(request, section_id):
    """Créer une nouvelle tâche dans une section."""
    section = get_object_or_404(Section, id=section_id)
    if not section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        logger.info("=== Début de la création de tâche ===")
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"Files in request.FILES: {request.FILES}")
        for key, file in request.FILES.items():
            logger.info(f"File '{key}': name={file.name}, size={file.size}, content_type={file.content_type}")
        logger.info(f"POST data: {request.POST}")
        
        form = TaskForm(request.POST, request.FILES, section=section, fablab=section.view.fablab)
        if form.is_valid():
            logger.info("Form is valid")
            logger.info(f"Cleaned data: {form.cleaned_data}")
            try:
                task = form.save()
                logger.info("Task saved successfully")
                logger.info(f"Created task ID: {task.id}")
                if task.files.exists():
                    logger.info("Attached files:")
                    for file in task.files.all():
                        logger.info(f"- {file.filename} ({file.file_type}, {file.file_size} bytes)")
                messages.success(request, 'Tâche créée avec succès.')
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                return redirect('fabprojects:view_detail', view_id=section.view.id)
            except Exception as e:
                logger.error(f"Error saving task: {str(e)}", exc_info=True)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [str(e)]}
                    })
        else:
            logger.error(f"Form validation errors: {form.errors}")
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        form = TaskForm(section=section, fablab=section.view.fablab)
    
    context = {
        'form': form,
        'section': section,
        'title': 'Nouvelle Tâche'
    }
    if request.GET.get('panel'):
        return render(request, 'fabprojects/task_form_panel.html', context)
    return render(request, 'fabprojects/task_form.html', context)

@login_required
def task_edit(request, task_id):
    """Modifier une tâche existante."""
    logger.info("\n=== DÉBUT DE LA REQUÊTE D'ÉDITION DE TÂCHE ===")
    logger.info(f"Task ID: {task_id}")
    logger.info(f"User: {request.user.username} (ID: {request.user.id})")
    logger.info(f"Method: {request.method}")
    logger.info(f"Content-Type: {request.content_type}")
    
    task = get_object_or_404(Task, id=task_id)
    
    # Log des informations originales de la tâche
    logger.info("\n=== VALEURS ORIGINALES DE LA TÂCHE ===")
    logger.info(f"Titre: {task.title}")
    logger.info(f"Description: {task.description}")
    logger.info(f"Date limite: {task.deadline}")
    logger.info(f"Terminée: {task.is_completed}")
    
    # Log détaillé des tags originaux
    tags_originaux = list(task.tags.all())
    logger.info(f"Tags originaux ({len(tags_originaux)}):")
    for tag in tags_originaux:
        logger.info(f"  - ID: {tag.id}, Nom: {tag.name}, Couleur: {tag.color}")
    
    # Log des utilisateurs assignés originaux
    users_originaux = list(task.assigned_users.all())
    logger.info(f"Utilisateurs assignés originaux ({len(users_originaux)}):")
    for user in users_originaux:
        logger.info(f"  - ID: {user.id}, Username: {user.username}")
    
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        logger.warning(f"Accès refusé: l'utilisateur {request.user.username} n'a pas accès à cette tâche")
        raise PermissionDenied
    
    if request.method == 'POST':
        logger.info("\n=== DÉTAILS DE LA REQUÊTE POST ===")
        
        # Log des données POST spécifiques liées aux dates et tags
        logger.info("\n=== DONNÉES POST SPÉCIFIQUES ===")
        if 'deadline' in request.POST:
            logger.info(f"Deadline soumise: {request.POST.get('deadline')}")
        else:
            logger.info("Aucune deadline soumise")
            
        if 'tags' in request.POST:
            tags_soumis = request.POST.getlist('tags')
            logger.info(f"Tags soumis: {tags_soumis}")
        else:
            logger.info("Aucun tag soumis")
        
        logger.info(f"POST data complète: {dict(request.POST)}")
        logger.info(f"FILES data: {dict(request.FILES)}")
        
        form = TaskForm(request.POST, request.FILES, instance=task, section=task.section)
        logger.info(f"Formulaire créé avec succès")
        
        if form.is_valid():
            logger.info("\n=== FORMULAIRE VALIDE ===")
            logger.info(f"Cleaned data: {form.cleaned_data}")
            
            # Log détaillé des dates et tags validés
            if 'deadline' in form.cleaned_data:
                logger.info(f"Date limite validée: {form.cleaned_data.get('deadline')}")
            
            if 'tags' in form.cleaned_data:
                tags_valides = list(form.cleaned_data.get('tags', []))
                logger.info(f"Tags validés ({len(tags_valides)}):")
                for tag in tags_valides:
                    logger.info(f"  - ID: {tag.id}, Nom: {tag.name}, Couleur: {tag.color}")
                
                # Identifier les tags ajoutés et supprimés
                tags_ajoutes = [tag for tag in tags_valides if tag not in tags_originaux]
                tags_supprimes = [tag for tag in tags_originaux if tag not in tags_valides]
                
                if tags_ajoutes:
                    logger.info(f"Tags ajoutés ({len(tags_ajoutes)}):")
                    for tag in tags_ajoutes:
                        logger.info(f"  + ID: {tag.id}, Nom: {tag.name}, Couleur: {tag.color}")
                
                if tags_supprimes:
                    logger.info(f"Tags supprimés ({len(tags_supprimes)}):")
                    for tag in tags_supprimes:
                        logger.info(f"  - ID: {tag.id}, Nom: {tag.name}, Couleur: {tag.color}")
            
            try:
                task = form.save()
                logger.info("\n=== TÂCHE SAUVEGARDÉE AVEC SUCCÈS ===")
                logger.info(f"ID de la tâche: {task.id}")
                logger.info(f"Titre: {task.title}")
                logger.info(f"Date limite: {task.deadline}")
                logger.info(f"Terminée: {task.is_completed}")
                
                # Log des tags finaux
                tags_finaux = list(task.tags.all())
                logger.info(f"Tags finaux ({len(tags_finaux)}):")
                for tag in tags_finaux:
                    logger.info(f"  - ID: {tag.id}, Nom: {tag.name}, Couleur: {tag.color}")
                
                # Log des utilisateurs assignés finaux
                users_finaux = list(task.assigned_users.all())
                logger.info(f"Utilisateurs assignés finaux ({len(users_finaux)}):")
                for user in users_finaux:
                    logger.info(f"  - ID: {user.id}, Username: {user.username}")
                
                if task.files.exists():
                    logger.info("\n=== FICHIERS ATTACHÉS ===")
                    for file in task.files.all():
                        logger.info(f"- {file.filename} ({file.file_type}, {file.file_size} bytes)")
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': True})
                
                messages.success(request, 'Tâche modifiée avec succès.')
                return redirect('fabprojects:task_detail', task_id=task.id)
            except Exception as e:
                logger.error("\n=== ERREUR LORS DE LA SAUVEGARDE ===")
                logger.error(f"Type d'erreur: {type(e)}")
                logger.error(f"Message d'erreur: {str(e)}")
                logger.error("Traceback:", exc_info=True)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': False,
                        'errors': {'__all__': [str(e)]}
                    })
        else:
            logger.error("\n=== ERREURS DE VALIDATION DU FORMULAIRE ===")
            logger.error(f"Erreurs: {form.errors}")
            
            # Log détaillé des erreurs spécifiques aux dates et tags
            if 'deadline' in form.errors:
                logger.error(f"Erreurs de date limite: {form.errors['deadline']}")
            
            if 'tags' in form.errors:
                logger.error(f"Erreurs de tags: {form.errors['tags']}")
            
            logger.error(f"Erreurs non liées aux champs: {form.non_field_errors()}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'errors': form.errors
                })
    else:
        logger.info("\n=== REQUÊTE GET - CHARGEMENT DU FORMULAIRE ===")
        # Passer explicitement le fablab au formulaire pour s'assurer que les tags sont correctement filtrés
        fablab = task.section.view.fablab
        logger.info(f"FabLab récupéré: {fablab.name} (ID: {fablab.id})")
        form = TaskForm(instance=task, section=task.section, fablab=fablab)
        
        # Vérifier que les tags sont correctement chargés
        for field_name, field in form.fields.items():
            if field_name == 'tags':
                logger.info(f"Champ {field_name} - queryset contient {field.queryset.count()} tags")
                logger.info(f"Tags disponibles dans la liste: {[f'{t.id}:{t.name}' for t in field.queryset]}")
    
    context = {
        'form': form,
        'task': task,
        'title': 'Modifier la Tâche'
    }
    
    # Ajouter les données des tags pour le JavaScript
    if task:
        tags_data = []
        for tag in task.tags.all():
            tags_data.append({
                'id': tag.id,
                'name': tag.name,
                'color': tag.color or "#cccccc"
            })
        context['tags_data_json'] = json.dumps(tags_data)
    
    logger.info("\n=== FIN DE LA REQUÊTE D'ÉDITION DE TÂCHE ===")
    
    if request.GET.get('panel'):
        return render(request, 'fabprojects/task_form_panel.html', context)
    return render(request, 'fabprojects/task_form.html', context)

@login_required
def task_detail(request, task_id):
    """Afficher le détail d'une tâche."""
    task = get_object_or_404(Task, id=task_id)
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    context = {
        'task': task,
        'subtasks': task.subtasks.all(),
        'custom_fields': task.custom_field_values.all(),
    }
    return render(request, 'fabprojects/task_detail.html', context)

@login_required
def task_delete(request, task_id):
    """Supprimer une tâche."""
    task = get_object_or_404(Task, id=task_id)
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        view_id = task.section.view.id
        task.delete()
        messages.success(request, 'Tâche supprimée avec succès.')
        return redirect('fabprojects:view_detail', view_id=view_id)
    
    context = {
        'task': task,
    }
    return render(request, 'fabprojects/task_confirm_delete.html', context)

@login_required
def subtask_create(request, task_id):
    """Créer une nouvelle sous-tâche."""
    task = get_object_or_404(Task, id=task_id)
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = SubTaskForm(request.POST)
        if form.is_valid():
            subtask = form.save(commit=False)
            subtask.task = task
            subtask.save()
            messages.success(request, 'Sous-tâche créée avec succès.')
            return redirect('fabprojects:task_detail', task_id=task.id)
    else:
        form = SubTaskForm()
    
    context = {
        'form': form,
        'task': task,
        'title': 'Nouvelle Sous-tâche'
    }
    return render(request, 'fabprojects/subtask_form.html', context)

@login_required
def subtask_edit(request, subtask_id):
    """Modifier une sous-tâche existante."""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    if not subtask.task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = SubTaskForm(request.POST, instance=subtask)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sous-tâche modifiée avec succès.')
            return redirect('fabprojects:task_detail', task_id=subtask.task.id)
    else:
        form = SubTaskForm(instance=subtask)
    
    context = {
        'form': form,
        'subtask': subtask,
        'title': 'Modifier la Sous-tâche'
    }
    return render(request, 'fabprojects/subtask_form.html', context)

@login_required
def subtask_delete(request, subtask_id):
    """Supprimer une sous-tâche."""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    if not subtask.task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        task_id = subtask.task.id
        subtask.delete()
        messages.success(request, 'Sous-tâche supprimée avec succès.')
        return redirect('fabprojects:task_detail', task_id=task_id)
    
    context = {
        'subtask': subtask,
    }
    return render(request, 'fabprojects/subtask_confirm_delete.html', context)

@login_required
def subtask_toggle_complete(request, subtask_id):
    """Basculer l'état de complétion d'une sous-tâche."""
    subtask = get_object_or_404(SubTask, id=subtask_id)
    if not subtask.task.section.view.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    subtask.is_completed = not subtask.is_completed
    subtask.save()
    
    return JsonResponse({
        'status': 'success',
        'is_completed': subtask.is_completed
    })

@login_required
def tag_list(request):
    """Liste des tags."""
    user_fablabs = request.user.fablabs.all()
    tags = Tag.objects.filter(fablab__in=user_fablabs).select_related('fablab').order_by('fablab__name', 'name')
    
    context = {
        'tags': tags,
    }
    return render(request, 'fabprojects/tag_list.html', context)

@login_required
def tag_create(request):
    """Créer un nouveau tag."""
    if request.method == 'POST':
        form = TagForm(request.POST, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag créé avec succès pour tous vos FabLabs.')
            return redirect('fabprojects:tag_list')
    else:
        form = TagForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Nouveau Tag'
    }
    return render(request, 'fabprojects/tag_form.html', context)

@login_required
def tag_edit(request, tag_id):
    """Modifier un tag existant."""
    tag = get_object_or_404(Tag, id=tag_id)
    if not tag.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = TagForm(request.POST, instance=tag, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Tag modifié avec succès pour tous vos FabLabs.')
            return redirect('fabprojects:tag_list')
    else:
        form = TagForm(instance=tag, user=request.user)
    
    context = {
        'form': form,
        'tag': tag,
        'title': 'Modifier le Tag'
    }
    return render(request, 'fabprojects/tag_form.html', context)

@login_required
def tag_delete(request, tag_id):
    """Supprimer un tag."""
    tag = get_object_or_404(Tag, id=tag_id)
    if not tag.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        tag.delete()
        messages.success(request, 'Tag supprimé avec succès.')
        return redirect('fabprojects:tag_list')
    
    context = {
        'tag': tag,
    }
    return render(request, 'fabprojects/tag_confirm_delete.html', context)

@login_required
def custom_field_list(request):
    """Liste des champs personnalisés."""
    user_fablabs = request.user.fablabs.all()
    custom_fields = CustomField.objects.filter(fablab__in=user_fablabs)
    
    context = {
        'custom_fields': custom_fields,
    }
    return render(request, 'fabprojects/custom_field_list.html', context)

@login_required
def custom_field_create(request):
    """Créer un nouveau champ personnalisé."""
    if request.method == 'POST':
        form = CustomFieldForm(request.POST, user=request.user)
        if form.is_valid():
            custom_field = form.save()
            messages.success(request, 'Champ personnalisé créé avec succès.')
            return redirect('fabprojects:custom_field_list')
    else:
        form = CustomFieldForm(user=request.user)
    
    context = {
        'form': form,
        'title': 'Nouveau Champ Personnalisé'
    }
    return render(request, 'fabprojects/custom_field_form.html', context)

@login_required
def custom_field_edit(request, field_id):
    """Modifier un champ personnalisé existant."""
    custom_field = get_object_or_404(CustomField, id=field_id)
    if not custom_field.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        form = CustomFieldForm(request.POST, instance=custom_field, user=request.user)
        if form.is_valid():
            old_type = custom_field.field_type
            new_type = form.cleaned_data['field_type']
            
            # Si le type a changé, convertir les valeurs existantes
            if old_type != new_type:
                try:
                    with transaction.atomic():
                        # Sauvegarder le nouveau type
                        custom_field = form.save()
                        
                        # Récupérer toutes les valeurs existantes
                        field_values = CustomFieldValue.objects.filter(field=custom_field)
                        
                        for field_value in field_values:
                            old_value = field_value.value
                            new_value = None
                            
                            # Conversion selon le nouveau type
                            if new_type == 'boolean':
                                # Convertir en booléen
                                if old_value and old_value.lower() not in ['false', '0', 'non', '']:
                                    new_value = 'true'
                                else:
                                    new_value = 'false'
                                    
                            elif new_type == 'number':
                                # Tenter de convertir en nombre
                                try:
                                    float_value = float(old_value)
                                    new_value = str(float_value)
                                except (ValueError, TypeError):
                                    new_value = '0'
                                    
                            elif new_type == 'date':
                                # Tenter de convertir en date
                                try:
                                    if old_type == 'text':
                                        # Essayer plusieurs formats de date courants
                                        for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y']:
                                            try:
                                                date_obj = datetime.strptime(old_value, date_format)
                                                new_value = date_obj.strftime('%Y-%m-%d')
                                                break
                                            except ValueError:
                                                continue
                                    if not new_value:
                                        new_value = timezone.now().strftime('%Y-%m-%d')
                                except:
                                    new_value = timezone.now().strftime('%Y-%m-%d')
                                    
                            elif new_type == 'choice':
                                # Pour les choix, vérifier si l'ancienne valeur est dans les nouvelles options
                                choices = [c.strip() for c in custom_field.choices.split('\n') if c.strip()]
                                if old_value in choices:
                                    new_value = old_value
                                elif choices:
                                    new_value = choices[0]  # Prendre la première option par défaut
                                else:
                                    new_value = ''
                                    
                            else:  # text
                                # Convertir en texte (tous les types peuvent être convertis en texte)
                                new_value = str(old_value) if old_value else ''
                            
                            # Mettre à jour la valeur
                            if new_value is not None:
                                field_value.value = new_value
                                field_value.save()
                            
                        messages.success(request, 'Champ personnalisé modifié avec succès. Les valeurs existantes ont été converties.')
                        return redirect('fabprojects:custom_field_list')
                        
                except Exception as e:
                    messages.error(request, f'Erreur lors de la conversion des valeurs : {str(e)}')
                    return redirect('fabprojects:custom_field_edit', field_id=field_id)
            else:
                # Si le type n'a pas changé, sauvegarder normalement
                form.save()
                messages.success(request, 'Champ personnalisé modifié avec succès.')
                return redirect('fabprojects:custom_field_list')
    else:
        form = CustomFieldForm(instance=custom_field, user=request.user)
    
    context = {
        'form': form,
        'custom_field': custom_field,
        'title': 'Modifier le Champ Personnalisé'
    }
    return render(request, 'fabprojects/custom_field_form.html', context)

@login_required
def custom_field_delete(request, field_id):
    """Supprimer un champ personnalisé."""
    custom_field = get_object_or_404(CustomField, id=field_id)
    if not custom_field.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    if request.method == 'POST':
        custom_field.delete()
        messages.success(request, 'Champ personnalisé supprimé avec succès.')
        return redirect('fabprojects:custom_field_list')
    
    context = {
        'custom_field': custom_field,
    }
    return render(request, 'fabprojects/custom_field_confirm_delete.html', context)

def project_context(request):
    """Context processor pour ajouter les vues aux templates."""
    if request.user.is_authenticated:
        user_fablabs = request.user.fablabs.all()
        views = View.objects.filter(fablab__in=user_fablabs).select_related('fablab').order_by('fablab__name', 'name')
        return {
            'user_views': views
        }
    return {}

@login_required
def task_move(request, task_id):
    """Déplacer une tâche vers une autre section et mettre à jour son ordre."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Method not allowed'})

    if not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': False, 'error': 'Invalid request'})

    task = get_object_or_404(Task, id=task_id)
    if not task.section.view.fablab.users.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'error': 'Permission denied'})

    try:
        data = json.loads(request.body)
        new_section_id = data.get('section_id')
        new_order = data.get('order')

        if new_section_id is None:
            return JsonResponse({'success': False, 'error': 'Missing section_id'})

        new_section = get_object_or_404(Section, id=new_section_id)
        if not new_section.view.fablab.users.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Permission denied'})

        # Vérifier que les sections appartiennent à la même vue
        if task.section.view_id != new_section.view_id:
            return JsonResponse({'success': False, 'error': 'Cannot move task between different views'})

        # Sauvegarder l'ancienne section pour réorganiser ses tâches
        old_section = task.section

        # Mettre à jour la section et l'ordre
        task.section = new_section
        task.order = new_order
        task.save()

        # Réorganiser les tâches dans l'ancienne section
        if old_section != new_section:
            old_tasks = Task.objects.filter(section=old_section).exclude(id=task.id).order_by('order')
            for index, old_task in enumerate(old_tasks):
                old_task.order = index
                old_task.save()

        # Réorganiser les tâches dans la nouvelle section
        new_tasks = Task.objects.filter(section=new_section).exclude(id=task.id).order_by('order')
        for index, other_task in enumerate(new_tasks):
            if index >= new_order:
                other_task.order = index + 1
                other_task.save()

        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid JSON'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def tag_autocomplete(request):
    """Endpoint pour l'autocomplétion des tags."""
    q = request.GET.get('q', '')
    logger.info(f"\n=== REQUÊTE TAG_AUTOCOMPLETE ===")
    logger.info(f"Terme de recherche: '{q}'")
    logger.info(f"Utilisateur: {request.user.username} (ID: {request.user.id})")
    
    user_fablabs = request.user.fablabs.all()
    logger.info(f"FabLabs de l'utilisateur: {[fl.name for fl in user_fablabs]}")
    
    tags = Tag.objects.filter(fablab__in=user_fablabs)
    
    if q:
        tags = tags.filter(name__icontains=q)
        logger.info(f"Filtrage par nom contenant '{q}': {tags.count()} résultats")
    else:
        logger.info(f"Aucun filtre de recherche: {tags.count()} résultats")
    
    results = [{'id': tag.id, 'text': tag.name, 'color': tag.color} for tag in tags[:10]]
    
    logger.info(f"\n=== JSON ENVOYÉ AU CLIENT ===")
    logger.info(f"Nombre de tags: {len(results)}")
    for i, tag_data in enumerate(results):
        logger.info(f"Tag {i+1}:")
        logger.info(f"  - id: {tag_data['id']}")
        logger.info(f"  - text: '{tag_data['text']}'")
        logger.info(f"  - color: '{tag_data['color']}'")
    
    return JsonResponse({'results': results})

@login_required
def tag_tasks(request, tag_id):
    """Liste des tâches associées à un tag."""
    tag = get_object_or_404(Tag, id=tag_id)
    if not tag.fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    # Récupérer toutes les tâches avec ce tag dans les FabLabs de l'utilisateur
    user_fablabs = request.user.fablabs.all()
    tasks = Task.objects.filter(
        tags=tag,
        section__view__fablab__in=user_fablabs
    ).select_related(
        'section__view__fablab'
    ).order_by('deadline')
    
    context = {
        'tag': tag,
        'tasks': tasks,
        'now': timezone.now().date(),
    }
    return render(request, 'fabprojects/tag_tasks.html', context)

@login_required
def custom_field_list_json(request):
    """Retourne la liste des champs personnalisés d'un FabLab au format JSON."""
    fablab_id = request.GET.get('fablab')
    if not fablab_id:
        return JsonResponse({'custom_fields': []})
    
    fablab = get_object_or_404(FabLab, id=fablab_id)
    if not fablab.users.filter(id=request.user.id).exists():
        raise PermissionDenied
    
    custom_fields = CustomField.objects.filter(fablab=fablab)
    data = {
        'custom_fields': [
            {
                'id': field.id,
                'name': field.name,
                'field_type': field.field_type
            }
            for field in custom_fields
        ]
    }
    return JsonResponse(data)

@login_required
@require_POST
def update_custom_field(request):
    """Met à jour la valeur d'un champ personnalisé pour une tâche."""
    from django.db import transaction
    
    try:
        with transaction.atomic():
            # Charger les données JSON
            data = json.loads(request.body)
            task_id = data.get('task_id')
            field_id = data.get('field_id')
            value = data.get('value', '')  # Valeur par défaut vide si non fournie

            # Vérifier que les données requises sont présentes
            if not all([task_id, field_id]):
                return JsonResponse({'success': False, 'error': 'Données manquantes'})

            # Récupérer la tâche et le champ
            task = Task.objects.select_for_update().get(id=task_id)
            field = CustomField.objects.get(id=field_id)

            # Vérifier que l'utilisateur a accès à la tâche
            if not task.section.view.fablab in request.user.fablabs.all():
                return JsonResponse({'success': False, 'error': 'Accès non autorisé'})

            # Vérifier que le champ appartient à la vue
            if field not in task.section.view.custom_fields.all():
                return JsonResponse({'success': False, 'error': 'Champ invalide'})

            # Initialiser formatted_value avec une valeur par défaut
            formatted_value = '-'

            # Si la valeur est vide, supprimer l'entrée existante
            if not value:
                CustomFieldValue.objects.filter(task=task, field=field).delete()
            else:
                # Valider et formater la valeur selon le type de champ
                if field.field_type == 'boolean':
                    if value not in ['true', 'false']:
                        return JsonResponse({'success': False, 'error': 'Valeur invalide pour un champ booléen'})
                    formatted_value = 'Oui' if value == 'true' else 'Non'
                    
                elif field.field_type == 'number':
                    try:
                        float(value)
                        formatted_value = value
                    except (ValueError, TypeError):
                        return JsonResponse({'success': False, 'error': 'Valeur invalide pour un champ numérique'})
                    
                elif field.field_type == 'date':
                    try:
                        date_obj = datetime.strptime(value, '%Y-%m-%d')
                        formatted_value = date_obj.strftime('%d/%m/%Y')
                    except (ValueError, TypeError):
                        return JsonResponse({'success': False, 'error': 'Format de date invalide'})
                    
                elif field.field_type == 'choice':
                    choices = [c.strip() for c in field.choices.split('\n')] if field.choices else []
                    if value not in choices:
                        return JsonResponse({'success': False, 'error': 'Choix invalide'})
                    formatted_value = value
                    
                else:  # text
                    formatted_value = value

                # Mettre à jour ou créer la valeur
                CustomFieldValue.objects.update_or_create(
                    task=task,
                    field=field,
                    defaults={'value': value}
                )

            return JsonResponse({
                'success': True,
                'formatted_value': formatted_value
            })

    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tâche introuvable'})
    except CustomField.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Champ introuvable'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def update_task_field(request):
    """Met à jour un champ d'une tâche."""
    try:
        # Charger les données JSON
        data = json.loads(request.body)
        task_id = data.get('task_id')
        field = data.get('field')
        value = data.get('value')

        # Vérifier que les données requises sont présentes
        if not all([task_id, field]):
            return JsonResponse({'success': False, 'error': 'Données manquantes'})

        # Récupérer la tâche
        task = Task.objects.select_for_update().get(id=task_id)

        # Vérifier que l'utilisateur a accès à la tâche
        if not task.section.view.fablab.users.filter(id=request.user.id).exists():
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})

        # Mettre à jour le champ approprié
        if field == 'title':
            if not value:
                return JsonResponse({'success': False, 'error': 'Le titre est requis'})
            task.title = value
            formatted_value = value
        
        elif field == 'deadline':
            if value:
                try:
                    task.deadline = datetime.strptime(value, '%Y-%m-%d')
                    formatted_value = task.deadline.strftime('%d/%m/%Y')
                except ValueError:
                    return JsonResponse({'success': False, 'error': 'Format de date invalide'})
            else:
                task.deadline = None
                formatted_value = '-'
        
        elif field == 'assigned_users':
            # value doit être une liste
            if not isinstance(value, list):
                return JsonResponse({'success': False, 'error': 'Format invalide pour les utilisateurs'})
            
            users = []
            if value:  # Si la liste n'est pas vide
                # Vérifier que tous les utilisateurs existent
                try:
                    user_ids = [int(uid) for uid in value]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': 'IDs utilisateurs invalides'})
                
                users = User.objects.filter(id__in=user_ids)
                if len(users) != len(user_ids):
                    return JsonResponse({'success': False, 'error': 'Certains utilisateurs sont introuvables'})
                
                # Vérifier que tous les utilisateurs appartiennent au FabLab
                fablab_users = task.section.view.fablab.users.all()
                invalid_users = [user for user in users if user not in fablab_users]
                if invalid_users:
                    return JsonResponse({
                        'success': False, 
                        'error': f'Les utilisateurs suivants n\'appartiennent pas au FabLab : {", ".join(u.username for u in invalid_users)}'
                    })

            # Mettre à jour les utilisateurs assignés
            task.assigned_users.set(users)
            formatted_value = [user.get_full_name() or user.username for user in users]

        elif field == 'tags':
            # value doit être une liste
            if not isinstance(value, list):
                return JsonResponse({'success': False, 'error': 'Format invalide pour les tags'})
            
            tags = []
            if value:  # Si la liste n'est pas vide
                # Vérifier que tous les tags existent
                try:
                    tag_ids = [int(tid) for tid in value]
                except (ValueError, TypeError):
                    return JsonResponse({'success': False, 'error': 'IDs tags invalides'})
                
                tags = Tag.objects.filter(id__in=tag_ids)
                if len(tags) != len(tag_ids):
                    return JsonResponse({'success': False, 'error': 'Certains tags sont introuvables'})

            # Mettre à jour les tags
            task.tags.set(tags)
            formatted_value = [{'name': tag.name, 'color': tag.color} for tag in tags]
        
        else:
            return JsonResponse({'success': False, 'error': 'Champ invalide'})

        task.save()

        return JsonResponse({
            'success': True,
            'formatted_value': formatted_value
        })

    except Task.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Tâche introuvable'})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Données JSON invalides'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def update_task_users(request, task_id):
    try:
        task = Task.objects.get(id=task_id)
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        
        # Vérifier que l'utilisateur a les droits sur cette tâche
        if not request.user.is_superuser and task.section.view.fablab not in request.user.fablabs.all():
            return JsonResponse({'status': 'error', 'message': 'Permission denied'}, status=403)
        
        # Mettre à jour les utilisateurs assignés
        task.assigned_users.set(user_ids)
        
        return JsonResponse({'status': 'success'})
    except Task.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Task not found'}, status=404)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@login_required
def check_tag_exists(request):
    name = request.GET.get('name', '').strip()
    tag_id = request.GET.get('tag_id')
    
    # Exclure le tag en cours d'édition de la vérification
    query = Tag.objects.filter(name__iexact=name)
    if tag_id:
        query = query.exclude(id=tag_id)
    
    exists = query.exists()
    return JsonResponse({'exists': exists})

@login_required
@require_POST
def task_file_delete(request, file_id):
    """Supprimer un fichier attaché à une tâche."""
    # Récupérer le fichier
    task_file = get_object_or_404(TaskFile, id=file_id)
    
    # Vérifier les permissions
    if not task_file.task.section.view.fablab.users.filter(id=request.user.id).exists():
        return JsonResponse({'success': False, 'error': 'Permission refusée'})
    
    try:
        # Supprimer le fichier
        task_file.delete()
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def section_detail(request, section_id):
    section = get_object_or_404(Section, id=section_id)
    view = section.view
    
    # Vérifier que l'utilisateur a accès au FabLab de cette vue
    if view.fablab not in request.user.fablabs.all():
        raise PermissionDenied
    
    context = {
        'view': view,
        'current_section': section,
        'sections': [section],  # Pour réutiliser le template existant
        'available_tags': Tag.objects.filter(fablab=view.fablab),
        'users': view.fablab.users.all(),
    }
    return render(request, 'fabprojects/view_detail.html', context)

@login_required
def section_update_tags(request, section_id):
    """Mettre à jour les tags d'une section."""
    section = get_object_or_404(Section, id=section_id)
    view = section.view
    
    # Vérifier que l'utilisateur a accès au FabLab de cette vue
    if view.fablab not in request.user.fablabs.all():
        raise PermissionDenied
    
    if request.method == 'POST':
        # Récupérer les IDs des tags sélectionnés
        tag_ids = request.POST.getlist('tags')
        
        # Récupérer les tags disponibles pour l'utilisateur
        user_fablabs = request.user.fablabs.all()
        available_tags = Tag.objects.filter(id__in=tag_ids, fablab__in=user_fablabs)
        
        # Mettre à jour les tags de la section
        section.tags.set(available_tags)
        
        messages.success(request, 'Tags mis à jour avec succès.')
        
        # Rediriger vers la vue détaillée de la section si on y était
        if request.GET.get('current_section'):
            return redirect('fabprojects:section_detail', section_id=section.id)
        return redirect('fabprojects:view_detail', view_id=view.id)
    
    return redirect('fabprojects:view_detail', view_id=view.id)

@login_required
def section_move(request, section_id):
    """
    Vue pour gérer le déplacement d'une section
    """
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'})
    
    try:
        section = get_object_or_404(Section, id=section_id)
        view = section.view
        
        # Vérifier que l'utilisateur a accès au FabLab
        if not request.user.fablabs.filter(id=view.fablab.id).exists():
            return JsonResponse({'success': False, 'error': 'Accès non autorisé'})
        
        data = json.loads(request.body)
        new_order = data.get('order')
        
        if new_order is None:
            return JsonResponse({'success': False, 'error': 'Ordre manquant'})
        
        # Mettre à jour l'ordre de la section
        sections = view.sections.all()
        sections = list(sections)
        sections.remove(section)
        sections.insert(new_order, section)
        
        # Mettre à jour l'ordre de toutes les sections
        for i, s in enumerate(sections):
            s.order = i
            s.save()
        
        return JsonResponse({'success': True})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
