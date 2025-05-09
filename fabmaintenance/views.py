from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test, permission_required
from django.utils import timezone
from django.contrib import messages
from django.http import Http404, JsonResponse
from django.conf import settings
from django.core.paginator import Paginator
from .models import (
    Machine, Maintenance, MaintenanceType, FabLab,
    MachineTemplate, MaintenanceTemplate, MachineType
)
from .forms import MachineForm, MaintenanceForm, UserRegistrationForm, MachineTemplateForm, MaintenanceTemplateForm
from django.contrib.auth import logout
import random
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.db.utils import IntegrityError
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.urls import reverse
import json

@login_required
def machine_list(request):
    """Vue principale listant les machines par FabLab."""
    # Récupérer le FabLab sélectionné depuis l'URL
    selected_fablab_id = request.GET.get('fablab')
    selected_fablab = None
    
    # Si un FabLab est sélectionné, vérifier que l'utilisateur y a accès
    if selected_fablab_id:
        try:
            selected_fablab = FabLab.objects.get(id=selected_fablab_id)
            if not request.user.is_superuser and selected_fablab not in request.user.fablabs.all():
                messages.error(request, "Vous n'avez pas accès à ce FabLab.")
                return redirect('fabmaintenance:machine_list')
        except FabLab.DoesNotExist:
            messages.error(request, "FabLab non trouvé.")
            return redirect('fabmaintenance:machine_list')
    
    # Filtrer par les FabLabs de l'utilisateur
    fablabs = request.user.fablabs.all()
    if selected_fablab and request.user.is_superuser:
        fablabs = [selected_fablab]
    
    fablabs_with_machines = []
    for fablab in fablabs:
        machines = Machine.objects.filter(fablab=fablab)
        for machine in machines:
            machine.upcoming_maintenance = Maintenance.objects.filter(
                machine=machine,
                completed_date__isnull=True,
                scheduled_date__lte=timezone.now() + timezone.timedelta(days=7)
            )
        # Ajouter tous les FabLabs, même ceux sans machines
        fablabs_with_machines.append({
            'fablab': fablab,
            'machines': machines
        })
    
    return render(request, 'fabmaintenance/machine_list.html', {
        'fablabs_with_machines': fablabs_with_machines,
        'MEDIA_URL': settings.MEDIA_URL,
        'selected_fablab': selected_fablab
    })

@login_required
def machine_detail(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if machine.fablab not in request.user.fablabs.all():
        raise Http404
    
    completed_maintenance = Maintenance.objects.filter(
        machine=machine,
        completed_date__isnull=False
    ).order_by('-completed_date')
    
    # Pagination des maintenances complétées
    paginator = Paginator(completed_maintenance, 20)  # 20 maintenances par page
    page_number = request.GET.get('page')
    completed_maintenance_page = paginator.get_page(page_number)
    
    upcoming_maintenance = Maintenance.objects.filter(
        machine=machine,
        completed_date__isnull=True
    ).order_by('scheduled_date')
    
    return render(request, 'fabmaintenance/machine_detail.html', {
        'machine': machine,
        'completed_maintenance': completed_maintenance_page,
        'upcoming_maintenance': upcoming_maintenance
    })

@login_required
def machine_edit(request, pk):
    """Vue pour éditer une machine."""
    machine = get_object_or_404(Machine, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_superuser and machine.fablab not in request.user.fablabs.all():
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour éditer cette machine.")
        return redirect('fabmaintenance:machine_list')
    
    if request.method == 'POST':
        form = MachineForm(request.user, request.POST, request.FILES, instance=machine)
        if form.is_valid():
            # Si l'utilisateur est super user, on préserve le FabLab de la machine
            if request.user.is_superuser:
                machine = form.save(commit=False)
                machine.fablab = machine.fablab  # Garder le FabLab original
                machine.save()
            else:
                form.save()
            messages.success(request, 'Machine mise à jour avec succès.')
            return redirect('fabmaintenance:machine_list')
    else:
        form = MachineForm(request.user, instance=machine)
    
    return render(request, 'fabmaintenance/machine_form.html', {
        'form': form,
        'machine': machine,
        'title': 'Modifier la machine'
    })

@login_required
def machine_delete(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if not request.user.has_perm('fabmaintenance.delete_machine', machine):
        raise PermissionDenied
    
    if request.method == "POST":
        machine.delete()
        messages.success(request, f'La machine {machine.name} a été supprimée avec succès.')
        return redirect('fabmaintenance:machine_list')
    
    return render(request, 'fabmaintenance/machine_confirm_delete.html', {
        'machine': machine,
    })

@login_required
def add_maintenance(request, machine_pk):
    machine = get_object_or_404(Machine, pk=machine_pk)
    is_public = request.GET.get('public', '0') == '1'
    
    # Vérifier que l'utilisateur a accès à cette machine
    if not is_public and machine.fablab not in request.user.fablabs.all():
        raise Http404
    
    if request.method == 'POST':
        form = MaintenanceForm(machine=machine, data=request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.machine = machine
            
            # Si la maintenance est faite aujourd'hui, on la marque comme complétée
            if maintenance.scheduling_type == 'today':
                maintenance.completed_date = timezone.now()
                maintenance.completed_by = request.user if request.user.is_authenticated else None
                messages.success(request, 'Maintenance enregistrée comme effectuée aujourd\'hui.')
            else:
                messages.success(request, 'Maintenance programmée avec succès.')
            
            # Explicitly set the significant field from the form data
            maintenance.significant = form.cleaned_data.get('significant', False)
            
            maintenance.save()
            if is_public:
                return redirect('fabmaintenance:machine_public_view', pk=machine.pk)
            return redirect('fabmaintenance:machine_detail', pk=machine.pk)
    else:
        # Filtrer les types de maintenance pour n'afficher que ceux du template de la machine
        form = MaintenanceForm(machine=machine)
        maintenance_types = []
        if machine.template:
            # Créer des types de maintenance basés sur les maintenances du template
            for mt in machine.template.maintenance_templates.all():
                # Utiliser filter().first() au lieu de get_or_create pour éviter les doublons
                maintenance_type = MaintenanceType.objects.filter(
                    name=mt.name,
                    is_custom=False
                ).first()
                
                if not maintenance_type:
                    maintenance_type = MaintenanceType.objects.create(
                        name=mt.name,
                        description=mt.description,
                        period_days=mt.period_days,
                        is_custom=False,
                        priority=mt.priority,
                        instructions=mt.instructions,
                        required_tools=mt.required_tools
                    )
                
                maintenance_types.append(maintenance_type)
        
        form.fields['maintenance_type_choice'].choices = [
            (str(mt.id), str(mt)) for mt in maintenance_types
        ] + [('other', 'Autre...')]
    
    template = 'fabmaintenance/maintenance_form_public.html' if is_public else 'fabmaintenance/maintenance_form.html'
    return render(request, template, {
        'form': form,
        'machine': machine,
        'is_public': is_public,
        'title': f'Ajouter une maintenance - {machine.name}'
    })

@csrf_exempt
def complete_maintenance(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    
    # Vérifier si une maintenance de même type a déjà été validée aujourd'hui
    if maintenance.scheduling_type == 'periodic':
        today = timezone.now().date()
        existing_maintenance = Maintenance.objects.filter(
            machine=maintenance.machine,
            maintenance_type=maintenance.maintenance_type,
            scheduling_type='periodic',
            period_days=maintenance.period_days,
            completed_date__date=today
        ).exclude(pk=maintenance.pk).first()
        
        if existing_maintenance:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': 'Une maintenance de ce type a déjà été validée aujourd\'hui.'
                })
            messages.error(request, 'Une maintenance de ce type a déjà été validée aujourd\'hui.')
            return redirect('fabmaintenance:machine_detail', pk=maintenance.machine.pk)
    
    # Permettre à n'importe qui de marquer une maintenance comme terminée
    maintenance.completed_date = timezone.now()
    maintenance.completed_by = request.user if request.user.is_authenticated else None
    maintenance.save()
    
    # Si c'est une maintenance périodique, créer la prochaine occurrence
    if maintenance.scheduling_type == 'periodic' and maintenance.period_days:
        # Utiliser la date du jour comme base pour le calcul
        today = timezone.now().date()
        next_date = today + timezone.timedelta(days=maintenance.period_days)
        
        Maintenance.objects.create(
            machine=maintenance.machine,
            maintenance_type=maintenance.maintenance_type,
            scheduled_date=next_date,
            scheduling_type='periodic',
            period_days=maintenance.period_days,
            notes=f"Maintenance périodique (tous les {maintenance.period_days} jours)"
        )
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    messages.success(request, 'Maintenance marquée comme terminée.')
    
    # Rediriger vers la vue publique si l'utilisateur n'est pas connecté
    if not request.user.is_authenticated:
        return redirect('fabmaintenance:machine_public_view', pk=maintenance.machine.pk)
    return redirect('fabmaintenance:machine_detail', pk=maintenance.machine.pk)

def machine_public_view(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    completed_maintenance = Maintenance.objects.filter(
        machine=machine,
        completed_date__isnull=False
    ).order_by('-completed_date')
    
    upcoming_maintenance = Maintenance.objects.filter(
        machine=machine,
        completed_date__isnull=True
    ).order_by('scheduled_date')
    
    return render(request, 'fabmaintenance/machine_public_view.html', {
        'machine': machine,
        'completed_maintenance': completed_maintenance,
        'upcoming_maintenance': upcoming_maintenance
    })

@login_required
def delete_maintenance(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    if not request.user.is_superuser and maintenance.machine.fablab not in request.user.fablabs.all():
        raise Http404
    
    machine_pk = maintenance.machine.pk
    
    if maintenance.scheduling_type == 'periodic':
        # Supprimer toutes les maintenances futures de la mme série
        future_maintenances = Maintenance.objects.filter(
            machine=maintenance.machine,
            maintenance_type=maintenance.maintenance_type,
            scheduling_type='periodic',
            period_days=maintenance.period_days,
            scheduled_date__gte=maintenance.scheduled_date,
            completed_date__isnull=True
        )
        count = future_maintenances.count()
        future_maintenances.delete()
        messages.success(
            request, 
            f'{count} maintenance{"s" if count > 1 else ""} périodique{"s" if count > 1 else ""} supprimée{"s" if count > 1 else ""}'
        )
    else:
        maintenance.delete()
        messages.success(request, 'Maintenance supprimée')
    
    return redirect('fabmaintenance:machine_detail', pk=machine_pk)

def machine_create(request):
    if request.method == 'POST':
        form = MachineForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('machine_list')
    else:
        form = MachineForm()
    return render(request, 'fabmaintenance/machine_form.html', {'form': form})

def logout_view(request):
    logout(request)
    return redirect('login')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        form.request = request  # Passer la requête au formulaire
        if form.is_valid():
            # Vérifier si un FabLab avec le même nom existe déjà
            fablab_name = form.cleaned_data['fablab_name']
            if FabLab.objects.filter(name=fablab_name).exists():
                messages.error(request, f'Un FabLab avec le nom "{fablab_name}" existe déjà. '
                                     f'Si vous êtes membre de ce FabLab, veuillez contacter l\'administrateur '
                                     f'du FabLab ou l\'équipe ResFabrica à contact@resfabrica.fr pour être ajouté.')
                return render(request, 'fabmaintenance/register.html', {'form': form})
            
            user = form.save(commit=False)
            user.accepts_contact = form.cleaned_data['accept_contact']
            user.save()
            
            # Create and associate FabLab
            fablab = FabLab.objects.create(
                name=form.cleaned_data['fablab_name']
            )
            fablab.users.add(user)
            
            messages.success(request, 'Votre compte a été créé avec succès. Vous pouvez maintenant vous connecter.')
            return redirect('login')
    else:
        # Générer de nouveaux nombres pour le CAPTCHA
        num1 = random.randint(1, 10)
        num2 = random.randint(1, 10)
        request.session['captcha_num1'] = num1
        request.session['captcha_num2'] = num2
        form = UserRegistrationForm(initial={'captcha_label': f'Combien font {num1} + {num2} ?'})
    
    return render(request, 'fabmaintenance/register.html', {'form': form})

def terms_of_service(request):
    return render(request, 'fabmaintenance/terms.html')

def handler404(request, exception):
    """Vue personnalisée pour les erreurs 404."""
    return render(request, 'fabmaintenance/404.html', status=404)

@login_required
def machine_catalogue(request):
    """Vue du catalogue des templates de machines."""
    # Filtres
    machine_type = request.GET.get('type')
    manufacturer = request.GET.get('manufacturer')
    search = request.GET.get('search')

    templates = MachineTemplate.objects.all()

    if machine_type:
        templates = templates.filter(machine_type_id=machine_type)
    if manufacturer:
        templates = templates.filter(manufacturer=manufacturer)
    if search:
        templates = templates.filter(
            Q(name__icontains=search) |
            Q(model__icontains=search) |
            Q(manufacturer__icontains=search) |
            Q(description__icontains=search)
        )

    # Liste des filtres disponibles
    machine_types = MachineType.objects.all()
    manufacturers = MachineTemplate.objects.values_list('manufacturer', flat=True).distinct()

    context = {
        'templates': templates,
        'machine_types': machine_types,
        'manufacturers': manufacturers,
        'current_type': machine_type,
        'current_manufacturer': manufacturer,
        'search': search,
    }
    return render(request, 'fabmaintenance/machine_catalogue.html', context)

@login_required
def machine_template_detail(request, pk):
    """Vue détaillée d'un template de machine."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    maintenances = template.maintenance_templates.all().order_by('-priority', 'name')

    context = {
        'template': template,
        'maintenances': maintenances,
    }
    return render(request, 'fabmaintenance/machine_template_detail.html', context)

@login_required
def create_machine_from_template(request, pk):
    template = get_object_or_404(MachineTemplate, pk=pk)
    
    if request.method == 'POST':
        selected_maintenances = request.POST.getlist('maintenances')
        
        if not selected_maintenances:
            messages.error(request, 'Veuillez sélectionner au moins une maintenance.')
            return redirect('fabmaintenance:machine_template_detail', pk=pk)
        
        try:
            # Récupérer le FabLab de l'utilisateur
            user_fablab = request.user.fablabs.first()
            if not user_fablab:
                messages.error(request, "Vous n'avez pas de FabLab associé à votre compte.")
                return redirect('fabmaintenance:machine_template_detail', pk=pk)
            
            # Créer la machine
            machine = Machine.objects.create(
                name=request.POST.get('name'),
                machine_type=template.machine_type,
                fablab=user_fablab,
                serial_number=request.POST.get('serial_number'),
                template=template  # Lier la machine au template
            )
            
            # Copier l'image du template si elle existe
            if template.image:
                from django.core.files import File
                from tempfile import NamedTemporaryFile
                import os
                
                temp_image = NamedTemporaryFile(delete=True)
                temp_image.write(template.image.read())
                temp_image.flush()
                
                filename = os.path.basename(template.image.name)
                machine.image.save(filename, File(temp_image))
            
            # Créer les maintenances
            for maintenance_id in selected_maintenances:
                maintenance_template = MaintenanceTemplate.objects.get(pk=maintenance_id)
                
                # Créer le type de maintenance s'il n'existe pas
                maintenance_type = MaintenanceType.objects.filter(
                    name=maintenance_template.name,
                    is_custom=False
                ).first()
                
                if not maintenance_type:
                    maintenance_type = MaintenanceType.objects.create(
                        name=maintenance_template.name,
                        description=maintenance_template.description,
                        period_days=maintenance_template.period_days,
                        is_custom=False,
                        priority=maintenance_template.priority,
                        instructions=maintenance_template.instructions,
                        required_tools=maintenance_template.required_tools
                    )
                else:
                    # Mettre à jour les instructions et outils si nécessaire
                    if not maintenance_type.instructions or not maintenance_type.required_tools:
                        maintenance_type.instructions = maintenance_template.instructions
                        maintenance_type.required_tools = maintenance_template.required_tools
                        maintenance_type.save()

                # Calculer la date prévue
                if maintenance_template.period_days is not None:
                    scheduled_date = timezone.now() + timezone.timedelta(days=maintenance_template.period_days)
                    scheduling_type = 'periodic'
                else:
                    scheduled_date = timezone.now()
                    scheduling_type = 'scheduled'

                # Créer la maintenance
                maintenance = Maintenance.objects.create(
                    machine=machine,
                    maintenance_type=maintenance_type,
                    scheduled_date=scheduled_date,
                    scheduling_type=scheduling_type,
                    period_days=maintenance_template.period_days,
                    instructions=maintenance_template.instructions,
                    required_tools=maintenance_template.required_tools
                )
            
            messages.success(request, 'Machine créée avec succès.')
            return redirect('fabmaintenance:machine_detail', pk=machine.pk)
            
        except Exception as e:
            messages.error(request, f'Erreur lors de la création de la machine : {str(e)}')
            return redirect('fabmaintenance:machine_template_detail', pk=pk)
    else:
        form = MachineForm(request.user, from_template=True, initial={
            'machine_type': template.machine_type.id
        })

    return render(request, 'fabmaintenance/create_machine_from_template.html', {
        'form': form,
        'template': template,
        'maintenances': template.maintenance_templates.all()
    })

def is_superuser(user):
    return user.is_superuser

@login_required
@user_passes_test(is_superuser)
def machine_template_create(request):
    """Vue pour créer un nouveau template de machine."""
    if request.method == 'POST':
        form = MachineTemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save()
            
            # Traiter les maintenances inline
            maintenance_names = request.POST.getlist('maintenance_name[]')
            maintenance_descriptions = request.POST.getlist('maintenance_description[]')
            maintenance_periods = request.POST.getlist('maintenance_period[]')
            
            # Créer les maintenances
            for i in range(len(maintenance_names)):
                if maintenance_names[i]:  # Ne créer que si le nom est fourni
                    MaintenanceTemplate.objects.create(
                        machine_template=template,
                        name=maintenance_names[i],
                        description=maintenance_descriptions[i] if i < len(maintenance_descriptions) else '',
                        period_days=int(maintenance_periods[i]) if i < len(maintenance_periods) else 30,
                        estimated_duration=timezone.timedelta(minutes=30),  # Valeur par défaut
                        priority=2,  # Priorité moyenne par défaut
                        instructions=''  # Instructions optionnelles
                    )
            
            messages.success(request, f'Le template {template.name} a été créé avec succès.')
            return redirect('fabmaintenance:machine_template_detail', pk=template.pk)
    else:
        form = MachineTemplateForm()
    
    return render(request, 'fabmaintenance/machine_template_form.html', {
        'form': form,
        'title': 'Créer un template de machine',
        'submit_text': 'Créer'
    })

@login_required
@user_passes_test(is_superuser)
def machine_template_edit(request, pk):
    """Vue pour modifier un template de machine."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    
    if request.method == 'POST':
        form = MachineTemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            template = form.save()
            
            # Supprimer toutes les maintenances existantes
            template.maintenance_templates.all().delete()
            
            # Traiter les maintenances inline
            maintenance_names = request.POST.getlist('maintenance_name[]')
            maintenance_descriptions = request.POST.getlist('maintenance_description[]')
            maintenance_periods = request.POST.getlist('maintenance_period[]')
            maintenance_priorities = request.POST.getlist('maintenance_priority[]')
            maintenance_instructions = request.POST.getlist('maintenance_instructions[]')
            maintenance_tools = request.POST.getlist('maintenance_tools[]')
            
            # Créer les nouvelles maintenances
            for i in range(len(maintenance_names)):
                if maintenance_names[i]:  # Ne créer que si le nom est fourni
                    MaintenanceTemplate.objects.create(
                        machine_template=template,
                        name=maintenance_names[i],
                        description=maintenance_descriptions[i] if i < len(maintenance_descriptions) else '',
                        period_days=int(maintenance_periods[i]) if i < len(maintenance_periods) else 30,
                        estimated_duration=timezone.timedelta(minutes=30),  # Valeur par défaut
                        priority=int(maintenance_priorities[i]) if i < len(maintenance_priorities) else 2,
                        instructions=maintenance_instructions[i] if i < len(maintenance_instructions) else '',
                        required_tools=maintenance_tools[i] if i < len(maintenance_tools) else ''
                    )
            
            messages.success(request, f'Le template {template.name} a été modifié avec succès.')
            return redirect('fabmaintenance:machine_template_detail', pk=template.pk)
    else:
        form = MachineTemplateForm(instance=template)
    
    return render(request, 'fabmaintenance/machine_template_form.html', {
        'form': form,
        'template': template,
        'title': 'Modifier le template',
        'submit_text': 'Enregistrer'
    })

@login_required
@user_passes_test(is_superuser)
def machine_template_delete(request, pk):
    """Vue pour supprimer un template de machine."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    
    if request.method == 'POST':
        name = template.name
        template.delete()
        messages.success(request, f'Le template {name} a été supprimé avec succès.')
        return redirect('fabmaintenance:machine_catalogue')
    
    return render(request, 'fabmaintenance/machine_template_confirm_delete.html', {
        'template': template
    })

@login_required
@user_passes_test(is_superuser)
def template_maintenance_add(request, pk):
    """Vue pour ajouter une maintenance à un template."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    
    if request.method == 'POST':
        form = MaintenanceTemplateForm(request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.machine_template = template
            maintenance.save()
            messages.success(request, f'La maintenance {maintenance.name} a été ajoutée avec succès.')
            return redirect('fabmaintenance:machine_template_detail', pk=template.pk)
    else:
        form = MaintenanceTemplateForm()
    
    return render(request, 'fabmaintenance/maintenance_template_form.html', {
        'form': form,
        'template': template,
        'title': 'Ajouter une maintenance',
        'submit_text': 'Ajouter'
    })

@login_required
@user_passes_test(is_superuser)
def template_maintenance_edit(request, template_pk, pk):
    """Vue pour modifier une maintenance d'un template."""
    template = get_object_or_404(MachineTemplate, pk=template_pk)
    maintenance = get_object_or_404(MaintenanceTemplate, pk=pk, machine_template=template)
    
    if request.method == 'POST':
        form = MaintenanceTemplateForm(request.POST, instance=maintenance)
        if form.is_valid():
            maintenance = form.save()
            messages.success(request, f'La maintenance {maintenance.name} a été modifiée avec succès.')
            return redirect('fabmaintenance:machine_template_detail', pk=template.pk)
    else:
        form = MaintenanceTemplateForm(instance=maintenance)
    
    return render(request, 'fabmaintenance/maintenance_template_form.html', {
        'form': form,
        'template': template,
        'maintenance': maintenance,
        'title': f'Modifier {maintenance.name}',
        'submit_text': 'Enregistrer'
    })

@login_required
@user_passes_test(is_superuser)
def template_maintenance_delete(request, template_pk, pk):
    """Vue pour supprimer une maintenance d'un template."""
    template = get_object_or_404(MachineTemplate, pk=template_pk)
    maintenance = get_object_or_404(MaintenanceTemplate, pk=pk, machine_template=template)
    
    if request.method == 'POST':
        name = maintenance.name
        maintenance.delete()
        messages.success(request, f'La maintenance {name} a été supprimée avec succès.')
        return redirect('fabmaintenance:machine_template_detail', pk=template.pk)
    
    return render(request, 'fabmaintenance/maintenance_template_confirm_delete.html', {
        'template': template,
        'maintenance': maintenance
    })

@login_required
@user_passes_test(is_superuser)
def template_maintenance_list(request, pk):
    """Vue pour lister les maintenances d'un template."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    maintenances = template.maintenance_templates.all().order_by('-priority', 'name')
    
    return render(request, 'fabmaintenance/template_maintenance_list.html', {
        'template': template,
        'maintenances': maintenances
    })

@login_required
@permission_required('fabmaintenance.change_machinetemplate')
@csrf_exempt
def template_maintenance_ajax(request, template_pk):
    template = get_object_or_404(MachineTemplate, pk=template_pk)
    
    if request.method == 'POST':
        maintenance_id = request.POST.get('maintenance_id')
        period_days = request.POST.get('period_days')
        # Convertir une chaîne vide en None
        if period_days == '':
            period_days = None
        elif period_days is not None:
            period_days = int(period_days)

        if maintenance_id:
            maintenance = get_object_or_404(MaintenanceTemplate, pk=maintenance_id)
            maintenance.name = request.POST.get('name')
            maintenance.description = request.POST.get('description')
            maintenance.period_days = period_days
            maintenance.priority = request.POST.get('priority')
            maintenance.instructions = request.POST.get('instructions')
            maintenance.required_tools = request.POST.get('required_tools')
            maintenance.save()
        else:
            maintenance = MaintenanceTemplate.objects.create(
                machine_template=template,
                name=request.POST.get('name'),
                description=request.POST.get('description'),
                period_days=period_days,
                priority=request.POST.get('priority'),
                instructions=request.POST.get('instructions'),
                required_tools=request.POST.get('required_tools'),
                estimated_duration=timedelta(minutes=30)
            )
        
        return JsonResponse({
            'id': maintenance.id,
            'name': maintenance.name,
            'description': maintenance.description,
            'period_days': maintenance.period_days,
            'priority': maintenance.priority,
            'priority_display': maintenance.get_priority_display(),
            'instructions': maintenance.instructions,
            'required_tools': maintenance.required_tools
        })
    
    elif request.method == 'GET':
        maintenance_id = request.GET.get('id')
        if maintenance_id:
            maintenance = get_object_or_404(MaintenanceTemplate, pk=maintenance_id)
            return JsonResponse({
                'id': maintenance.id,
                'name': maintenance.name,
                'description': maintenance.description,
                'period_days': maintenance.period_days,
                'priority': maintenance.priority,
                'priority_display': maintenance.get_priority_display(),
                'instructions': maintenance.instructions,
                'required_tools': maintenance.required_tools
            })
    
    elif request.method == 'DELETE':
        maintenance_id = request.GET.get('id')
        if maintenance_id:
            maintenance = get_object_or_404(MaintenanceTemplate, pk=maintenance_id)
            maintenance.delete()
            return JsonResponse({'status': 'success'})
    
    return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
@permission_required('fabmaintenance.change_machine')
@csrf_exempt
def maintenance_ajax(request, machine_pk):
    try:
        machine = get_object_or_404(Machine, pk=machine_pk)
        
        if request.method == 'GET':
            maintenance_id = request.GET.get('id')
            if maintenance_id:
                try:
                    maintenance = get_object_or_404(Maintenance, pk=maintenance_id, machine=machine)
                    
                    response_data = {
                        'success': True,
                        'id': maintenance.id,
                        'maintenance_type': {
                            'id': maintenance.maintenance_type_id,
                            'name': maintenance.maintenance_type.name,
                            'description': maintenance.maintenance_type.description or '',
                            'instructions': maintenance.maintenance_type.instructions or '',
                            'required_tools': maintenance.maintenance_type.required_tools or ''
                        },
                        'scheduling_type': maintenance.scheduling_type,
                        'period_days': maintenance.period_days,
                        'description': maintenance.maintenance_type.description or '',
                        'scheduled_date': maintenance.scheduled_date.strftime('%Y-%m-%d') if maintenance.scheduled_date else None,
                        'instructions': maintenance.instructions or maintenance.maintenance_type.instructions or '',
                        'required_tools': maintenance.required_tools or maintenance.maintenance_type.required_tools or ''
                    }
                    return JsonResponse(response_data)
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'error': "ID de maintenance non fourni"
                }, status=400)
        
        elif request.method == 'POST':
            maintenance_id = request.POST.get('maintenance_id')
            maintenance_type_choice = request.POST.get('maintenance_type_choice')
            custom_type_name = request.POST.get('custom_type_name')
            scheduling_type = request.POST.get('scheduling_type')
            scheduled_date = request.POST.get('scheduled_date')
            period_days = request.POST.get('period_days')
            instructions = request.POST.get('instructions')
            required_tools = request.POST.get('required_tools')
            description = request.POST.get('description')
            
            # Convertir la date string en objet date
            from datetime import datetime
            if scheduled_date:
                try:
                    scheduled_date = datetime.strptime(scheduled_date, '%Y-%m-%d').date()
                except ValueError:
                    return JsonResponse({
                        'success': False,
                        'error': "Format de date invalide. Utilisez le format YYYY-MM-DD."
                    }, status=400)
            
            try:
                if maintenance_id:
                    maintenance = get_object_or_404(Maintenance, pk=maintenance_id, machine=machine)
                    
                    if maintenance_type_choice == 'other':
                        # Mettre à jour le type de maintenance existant
                        maintenance.maintenance_type.name = custom_type_name
                        maintenance.maintenance_type.description = description
                        maintenance.maintenance_type.save()
                    
                    maintenance.scheduling_type = scheduling_type
                    maintenance.scheduled_date = scheduled_date
                    maintenance.period_days = period_days if scheduling_type == 'periodic' else None
                    maintenance.instructions = instructions
                    maintenance.required_tools = required_tools
                    maintenance.save()
                    
                else:
                    if maintenance_type_choice == 'other':
                        maintenance_type = MaintenanceType.objects.create(
                            name=custom_type_name,
                            description=description,
                            is_custom=True,
                            priority=2  # Priorité moyenne par défaut
                        )
                    else:
                        return JsonResponse({
                            'success': False,
                            'error': "Le type de maintenance est requis."
                        }, status=400)
                    
                    maintenance = Maintenance.objects.create(
                        machine=machine,
                        maintenance_type=maintenance_type,
                        scheduling_type=scheduling_type,
                        scheduled_date=scheduled_date,
                        period_days=period_days if scheduling_type == 'periodic' else None,
                        instructions=instructions,
                        required_tools=required_tools
                    )
                
                response_data = {
                    'success': True,
                    'id': maintenance.id,
                    'maintenance_type': {
                        'id': maintenance.maintenance_type_id,
                        'name': maintenance.maintenance_type.name,
                        'description': maintenance.maintenance_type.description or '',
                        'instructions': maintenance.maintenance_type.instructions or '',
                        'required_tools': maintenance.maintenance_type.required_tools or ''
                    },
                    'scheduling_type': maintenance.scheduling_type,
                    'period_days': maintenance.period_days,
                    'description': maintenance.maintenance_type.description or '',
                    'scheduled_date': maintenance.scheduled_date.strftime('%Y-%m-%d') if maintenance.scheduled_date else None,
                    'instructions': maintenance.instructions or maintenance.maintenance_type.instructions or '',
                    'required_tools': maintenance.required_tools or maintenance.maintenance_type.required_tools or ''
                }
                return JsonResponse(response_data)
                
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                }, status=400)
        
        elif request.method == 'DELETE':
            maintenance_id = request.GET.get('id')
            if maintenance_id:
                try:
                    maintenance = get_object_or_404(Maintenance, pk=maintenance_id, machine=machine)
                    
                    # Si c'est une maintenance périodique, supprimer toutes les maintenances futures de la même série
                    if maintenance.scheduling_type == 'periodic':
                        future_maintenances = Maintenance.objects.filter(
                            machine=machine,
                            maintenance_type=maintenance.maintenance_type,
                            scheduling_type='periodic',
                            period_days=maintenance.period_days,
                            scheduled_date__gte=maintenance.scheduled_date,
                            completed_date__isnull=True
                        )
                        future_maintenances.delete()
                    else:
                        maintenance.delete()
                    
                    return JsonResponse({'success': True})
                except Exception as e:
                    return JsonResponse({
                        'success': False,
                        'error': str(e)
                    }, status=400)
            else:
                return JsonResponse({
                    'success': False,
                    'error': "ID de maintenance non fourni"
                }, status=400)
        
        return JsonResponse({
            'success': False,
            'error': 'Requête invalide'
        }, status=400)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)

@login_required
@permission_required('fabmaintenance.change_machine')
def get_maintenance_names(request):
    """Vue pour récupérer les noms de maintenance existants pour l'autocomplétion."""
    search = request.GET.get('q', '')
    machine_type_id = request.GET.get('machine_type_id')
    
    # Base de la requête
    query = MaintenanceTemplate.objects.all()
    
    # Filtrer par type de machine si spécifié
    if machine_type_id:
        query = query.filter(machine_template__machine_type_id=machine_type_id)
    
    # Filtrer par terme de recherche
    if search:
        query = query.filter(name__icontains=search)
    
    # Récupérer les informations complètes
    maintenances = query.values('name', 'description', 'period_days', 'priority', 'instructions', 'required_tools').distinct()
    
    # Formater les résultats
    results = [
        {
            'name': m['name'],
            'description': m['description'],
            'period_days': m['period_days'],
            'priority': m['priority'],
            'instructions': m['instructions'],
            'required_tools': m['required_tools']
        }
        for m in maintenances
    ]
    
    return JsonResponse(results, safe=False)

@login_required
@user_passes_test(is_superuser)
def machine_template_duplicate(request, pk):
    """Vue pour dupliquer un template de machine."""
    template = get_object_or_404(MachineTemplate, pk=pk)
    
    if request.method == 'POST':
        new_name = request.POST.get('name')
        
        # Vérifier si le nom existe déjà
        if MachineTemplate.objects.filter(name=new_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'Un template avec ce nom existe déjà.'
            })
        
        # Créer une copie du template
        new_template = MachineTemplate.objects.create(
            name=new_name,
            machine_type=template.machine_type,
            manufacturer=template.manufacturer,
            model=template.model,
            description=template.description,
            documentation_url=template.documentation_url
        )
        
        # Copier l'image si elle existe
        if template.image:
            from django.core.files import File
            from tempfile import NamedTemporaryFile
            import os
            
            temp_image = NamedTemporaryFile(delete=True)
            temp_image.write(template.image.read())
            temp_image.flush()
            
            filename = os.path.basename(template.image.name)
            new_template.image.save(filename, File(temp_image))
        
        # Copier les maintenances
        for maintenance in template.maintenance_templates.all():
            MaintenanceTemplate.objects.create(
                machine_template=new_template,
                name=maintenance.name,
                description=maintenance.description,
                period_days=maintenance.period_days,
                estimated_duration=maintenance.estimated_duration,
                priority=maintenance.priority,
                instructions=maintenance.instructions,
                required_tools=maintenance.required_tools
            )
        
        return JsonResponse({
            'success': True,
            'redirect_url': reverse('fabmaintenance:machine_template_detail', kwargs={'pk': new_template.pk})
        })
    
    return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)

@login_required
def maintenance_create(request, machine_id):
    """Vue pour créer une nouvelle maintenance."""
    machine = get_object_or_404(Machine, id=machine_id)
    fablab = machine.fablab
    
    # Vérifier les permissions
    if not request.user.is_superuser and machine.fablab not in request.user.fablabs.all():
        messages.error(request, "Vous n'avez pas les permissions nécessaires pour créer une maintenance sur cette machine.")
        return redirect('fabmaintenance:machine_list')
    
    if request.method == 'POST':
        form = MaintenanceForm(machine=machine, data=request.POST)
        if form.is_valid():
            maintenance = form.save(commit=False)
            maintenance.machine = machine
            maintenance.created_by = request.user
            maintenance.save()
            
            # Gérer les tags
            if 'tags' in form.cleaned_data:
                maintenance.tags.set(form.cleaned_data['tags'])
            
            messages.success(request, 'Maintenance créée avec succès.')
            return redirect('fabmaintenance:machine_detail', pk=machine.pk)
    else:
        form = MaintenanceForm(machine=machine)
    
    return render(request, 'fabmaintenance/maintenance_form.html', {
        'form': form,
        'machine': machine,
        'fablab': fablab
    })

@login_required
def machine_duplicate(request, pk):
    """Vue pour dupliquer une machine."""
    machine = get_object_or_404(Machine, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_superuser and machine.fablab not in request.user.fablabs.all():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        data = json.loads(request.body)
        new_name = data.get('name', f"{machine.name} (copie)")
        duplicate_maintenance = data.get('duplicate_maintenance', True)
        
        # Vérifier si le nom existe déjà dans le même FabLab
        if Machine.objects.filter(name=new_name, fablab=machine.fablab).exists():
            return JsonResponse({
                'success': False,
                'error': 'Une machine avec ce nom existe déjà dans ce FabLab'
            }, status=400)
        
        # Créer une copie de la machine
        new_machine = Machine.objects.create(
            name=new_name,
            machine_type=machine.machine_type,
            template=machine.template,
            fablab=machine.fablab,
            serial_number=f"{machine.serial_number} (copie)" if machine.serial_number else None,
            image=machine.image if machine.image else None
        )
        
        # Dupliquer les maintenances si demandé
        if duplicate_maintenance:
            for maintenance in machine.maintenance_set.all():
                new_maintenance = Maintenance.objects.create(
                    machine=new_machine,
                    maintenance_type=maintenance.maintenance_type,
                    scheduled_date=maintenance.scheduled_date,
                    notes=maintenance.notes,
                    scheduling_type=maintenance.scheduling_type,
                    period_days=maintenance.period_days,
                    custom_type_name=maintenance.custom_type_name,
                    significant=maintenance.significant,
                    instructions=maintenance.instructions,
                    required_tools=maintenance.required_tools
                )
        
        return JsonResponse({'success': True})
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

@login_required
def validate_maintenance(request, maintenance_id):
    """Vue pour valider une maintenance."""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode non autorisée'}, status=405)
    
    try:
        maintenance = Maintenance.objects.get(id=maintenance_id)
        
        # Vérifier que l'utilisateur a accès au FabLab
        if not request.user.is_superuser and maintenance.machine.fablab not in request.user.fablabs.all():
            return JsonResponse({'success': False, 'error': 'Permission refusée'}, status=403)
        
        # Vérifier que la maintenance n'est pas déjà validée
        if maintenance.completed_date:
            return JsonResponse({'success': False, 'error': 'Cette maintenance est déjà validée'}, status=400)
        
        # Valider la maintenance
        maintenance.completed_date = timezone.now()
        maintenance.completed_by = request.user
        maintenance.save()
        
        return JsonResponse({'success': True})
    except Maintenance.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Maintenance non trouvée'}, status=404)
