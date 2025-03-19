from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.contrib import messages
from django.http import Http404
from django.conf import settings
from django.core.paginator import Paginator
from .models import Machine, Maintenance, MaintenanceType, FabLab
from .forms import MachineForm, MaintenanceForm, UserRegistrationForm
from django.contrib.auth import logout
import random

@login_required
def machine_list(request):
    """Vue principale listant les machines par FabLab."""
    # Toujours filtrer par les FabLabs de l'utilisateur, même pour les administrateurs
    fablabs = request.user.fablabs.all()
    
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
        'MEDIA_URL': settings.MEDIA_URL
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
def machine_add(request):
    if request.method == 'POST':
        form = MachineForm(user=request.user, data=request.POST, files=request.FILES)
        if form.is_valid():
            machine = form.save()
            messages.success(request, 'Machine ajoutée avec succès.')
            return redirect('fabmaintenance:machine_detail', pk=machine.pk)
    else:
        form = MachineForm(user=request.user)
    
    return render(request, 'fabmaintenance/machine_form.html', {'form': form})

@login_required
def machine_edit(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if machine.fablab not in request.user.fablabs.all():
        raise Http404
    
    if request.method == 'POST':
        form = MachineForm(user=request.user, data=request.POST, files=request.FILES, instance=machine)
        if form.is_valid():
            machine = form.save()
            messages.success(request, 'Machine modifiée avec succès.')
            return redirect('fabmaintenance:machine_detail', pk=machine.pk)
    else:
        form = MachineForm(user=request.user, instance=machine)
    
    return render(request, 'fabmaintenance/machine_form.html', {'form': form})

@login_required
def machine_delete(request, pk):
    machine = get_object_or_404(Machine, pk=pk)
    if machine.fablab not in request.user.fablabs.all():
        raise Http404
    
    machine.delete()
    messages.success(request, 'Machine supprimée avec succès.')
    return redirect('fabmaintenance:machine_list')

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
        form = MaintenanceForm(machine=machine)
    
    template = 'fabmaintenance/maintenance_form_public.html' if is_public else 'fabmaintenance/maintenance_form.html'
    return render(request, template, {
        'form': form,
        'machine': machine,
        'is_public': is_public
    })

def complete_maintenance(request, pk):
    maintenance = get_object_or_404(Maintenance, pk=pk)
    # Permettre à n'importe qui de marquer une maintenance comme terminée
    maintenance.completed_date = timezone.now()
    maintenance.completed_by = request.user if request.user.is_authenticated else None
    maintenance.save()
    
    # Si c'est une maintenance périodique, créer la prochaine occurrence
    if maintenance.scheduling_type == 'periodic' and maintenance.period_days:
        next_date = maintenance.scheduled_date + timezone.timedelta(days=maintenance.period_days)
        Maintenance.objects.create(
            machine=maintenance.machine,
            maintenance_type=maintenance.maintenance_type,
            scheduled_date=next_date,
            scheduling_type='periodic',
            period_days=maintenance.period_days,
            notes=f"Maintenance périodique (tous les {maintenance.period_days} jours)"
        )
    
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
