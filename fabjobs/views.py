from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Q
from django.http import JsonResponse
from .models import Job, Material, JobFile, MachineType, FabLab
from fabmaintenance.models import Machine
from .forms import JobForm, MaterialForm, JobFileForm
import logging
import hashlib
from django.views.decorators.csrf import csrf_exempt
from django.db import models

logger = logging.getLogger(__name__)

@login_required
def job_list(request):
    """Liste des jobs"""
    # Récupérer les FabLabs de l'utilisateur
    user_fablabs = request.user.fablabs.all()
    
    # Filtrer par FabLab si l'utilisateur n'est pas superuser
    if request.user.is_superuser:
        jobs = Job.objects.filter(machine__fablab__in=user_fablabs)
        machines = Machine.objects.filter(fablab__in=user_fablabs)
        fablabs = user_fablabs
        machine_types = MachineType.objects.filter(
            machine__fablab__in=user_fablabs
        ).distinct()
    else:
        jobs = Job.objects.filter(machine__fablab__in=user_fablabs)
        machines = Machine.objects.filter(fablab__in=user_fablabs)
        fablabs = user_fablabs
        machine_types = MachineType.objects.filter(
            machine__fablab__in=user_fablabs
        ).distinct()

    # Filtres
    status = request.GET.get('status')
    if status:
        jobs = jobs.filter(status=status)

    machine_type = request.GET.get('machine_type')
    if machine_type:
        jobs = jobs.filter(machine__machine_type_id=machine_type)
        # Filtrer les machines disponibles en fonction du type sélectionné
        machines = machines.filter(machine_type_id=machine_type)

    machine = request.GET.get('machine')
    if machine:
        jobs = jobs.filter(machine_id=machine)
        # Récupérer la machine sélectionnée
        selected_machine_obj = machines.filter(id=machine).first()
        # Générer le hash public pour la machine sélectionnée
        if selected_machine_obj:
            public_hash = generate_public_url(selected_machine_obj)
    else:
        selected_machine_obj = None
        public_hash = None

    fablab = request.GET.get('fablab')
    if fablab:
        jobs = jobs.filter(machine__fablab_id=fablab)
        # Filtrer les machines disponibles en fonction du FabLab sélectionné
        machines = machines.filter(fablab_id=fablab)
        # Filtrer les types de machines disponibles pour ce FabLab
        machine_types = machine_types.filter(
            machine__fablab_id=fablab
        ).distinct()

    context = {
        'jobs': jobs.order_by('-created_at'),
        'status_choices': Job.STATUS_CHOICES,
        'machines': machines.order_by('name'),
        'machine_types': machine_types.order_by('name'),
        'fablabs': fablabs.order_by('name'),
        'selected_machine': machine,
        'selected_machine_obj': selected_machine_obj,
        'selected_machine_type': machine_type,
        'selected_fablab': fablab,
        'selected_status': status,
        'public_hash': public_hash,
    }
    return render(request, 'fabjobs/job_list.html', context)

@login_required
def job_detail(request, pk):
    """Détails d'un job"""
    job = get_object_or_404(Job, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_superuser and job.machine.fablab not in request.user.fablabs.all():
        messages.error(request, "Vous n'avez pas accès à ce job.")
        return redirect('fabjobs:job_list')

    if request.method == 'POST':
        form = JobFileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.job = job
            file.uploaded_by = request.user
            file.save()
            messages.success(request, "Fichier ajouté avec succès.")
            return redirect('fabjobs:job_detail', pk=job.pk)
    else:
        form = JobFileForm()

    context = {
        'job': job,
        'form': form,
        'files': job.files.all(),
    }
    return render(request, 'fabjobs/job_detail.html', context)

@login_required
def job_create(request):
    """Création d'un nouveau job"""
    if request.method == 'POST':
        # Récupérer la machine sélectionnée
        machine_id = request.POST.get('machine')
        if machine_id:
            machine = get_object_or_404(Machine, id=machine_id)
            # Précharger les matériaux compatibles
            materials = Material.objects.filter(
                machine_types=machine.machine_type,
                fablabs__in=request.user.fablabs.all()
            ).distinct()
            form = JobForm(user=request.user, data=request.POST, files=request.FILES)
            form.fields['material'].queryset = materials
        else:
            form = JobForm(user=request.user, data=request.POST, files=request.FILES)
        
        if form.is_valid():
            try:
                job = form.save(commit=False)
                job.created_by = request.user
                job.save()
                messages.success(request, "Job créé avec succès.")
                return redirect('fabjobs:job_detail', pk=job.pk)
            except Exception as e:
                messages.error(request, f"Erreur lors de la création du job: {str(e)}")
    else:
        form = JobForm(user=request.user)

    # Préparer les données utilisateur pour le template
    users = request.user.fablabs.first().users.all()
    user_data = {
        str(user.id): {
            'color': user.profile.avatar_color,
            'initials': user.get_initials(),
            'name': user.get_full_name() or user.username
        } for user in users
    }

    context = {
        'form': form,
        'title': "Nouveau job",
        'user_data': user_data
    }
    return render(request, 'fabjobs/job_form.html', context)

@login_required
def job_update(request, pk):
    """Modification d'un job"""
    job = get_object_or_404(Job, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_superuser and job.machine.fablab not in request.user.fablabs.all():
        messages.error(request, "Vous n'avez pas accès à ce job.")
        return redirect('fabjobs:job_list')

    if request.method == 'POST':
        form = JobForm(user=request.user, data=request.POST, files=request.FILES, instance=job)
        if form.is_valid():
            job = form.save()
            job.calculate_costs()  # Recalculer les coûts
            messages.success(request, "Job mis à jour avec succès.")
            return redirect('fabjobs:job_detail', pk=job.pk)
    else:
        form = JobForm(user=request.user, instance=job)

    # Préparer les données utilisateur pour le template
    users = request.user.fablabs.first().users.all()
    user_data = {
        str(user.id): {
            'color': user.profile.avatar_color,
            'initials': user.get_initials(),
            'name': user.get_full_name() or user.username
        } for user in users
    }

    context = {
        'form': form,
        'job': job,
        'title': f"Modifier {job.name}",
        'user_data': user_data
    }
    return render(request, 'fabjobs/job_form.html', context)

@login_required
def material_list(request):
    """Liste des matériaux"""
    # Filtrer par FabLab si l'utilisateur n'est pas superuser
    if request.user.is_superuser:
        materials = Material.objects.all()
    else:
        materials = Material.objects.filter(fablabs__in=request.user.fablabs.all())

    # Filtres
    machine_type = request.GET.get('machine_type')
    if machine_type:
        materials = materials.filter(machine_types__id=machine_type)

    fablab = request.GET.get('fablab')
    if fablab:
        materials = materials.filter(fablabs__id=fablab)

    # Récupérer les listes pour les filtres
    machine_types = MachineType.objects.all()
    # Ne montrer que les FabLabs de l'utilisateur
    fablabs = request.user.fablabs.all()

    context = {
        'materials': materials,
        'machine_types': machine_types,
        'fablabs': fablabs,
    }
    return render(request, 'fabjobs/material_list.html', context)

@login_required
def material_create(request):
    """Création d'un nouveau matériau"""
    if request.method == 'POST':
        form = MaterialForm(user=request.user, data=request.POST)
        if form.is_valid():
            material = form.save()
            messages.success(request, "Matériau créé avec succès.")
            return redirect('fabjobs:material_list')
    else:
        form = MaterialForm(user=request.user)

    context = {
        'form': form,
        'title': "Nouveau matériau",
    }
    return render(request, 'fabjobs/material_form.html', context)

@login_required
def material_update(request, pk):
    """Modification d'un matériau"""
    material = get_object_or_404(Material, pk=pk)
    
    # Vérifier les permissions
    if not request.user.is_superuser and material.fablab not in request.user.fablabs.all():
        messages.error(request, "Vous n'avez pas accès à ce matériau.")
        return redirect('fabjobs:material_list')

    if request.method == 'POST':
        form = MaterialForm(user=request.user, data=request.POST, instance=material)
        if form.is_valid():
            material = form.save()
            messages.success(request, "Matériau mis à jour avec succès.")
            return redirect('fabjobs:material_list')
    else:
        form = MaterialForm(user=request.user, instance=material)

    context = {
        'form': form,
        'material': material,
        'title': f"Modifier {material.name}",
    }
    return render(request, 'fabjobs/material_form.html', context)

@login_required
def material_delete(request, pk):
    """Suppression d'un matériau"""
    material = get_object_or_404(Material, pk=pk)
    
    # Vérifier les permissions (admin fablab ou superuser)
    if not (request.user.is_superuser or request.user.is_fablab_admin(material.fablab)):
        messages.error(request, "Vous n'avez pas les droits pour supprimer ce matériau.")
        return redirect('fabjobs:material_list')

    if request.method == 'POST':
        material.delete()
        messages.success(request, "Matériau supprimé avec succès.")
        return redirect('fabjobs:material_list')

    context = {
        'material': material,
        'title': f"Supprimer {material.name}",
    }
    return render(request, 'fabjobs/material_confirm_delete.html', context)

@login_required
def dashboard(request):
    """Tableau de bord des jobs"""
    # Filtrer par FabLab si l'utilisateur n'est pas superuser
    if request.user.is_superuser:
        jobs = Job.objects.all()
    else:
        jobs = Job.objects.filter(machine__fablab__in=request.user.fablabs.all())

    # Statistiques
    total_jobs = jobs.count()
    completed_jobs = jobs.filter(status='completed').count()
    pending_jobs = jobs.filter(status='pending').count()
    in_progress_jobs = jobs.filter(status='in_progress').count()

    # Coûts et CO2
    total_cost = jobs.filter(status='completed').aggregate(Sum('total_cost'))['total_cost__sum'] or 0
    total_co2 = jobs.filter(status='completed').aggregate(Sum('co2_emission'))['co2_emission__sum'] or 0

    # Jobs récents
    recent_jobs = jobs.order_by('-created_at')[:5]

    context = {
        'total_jobs': total_jobs,
        'completed_jobs': completed_jobs,
        'pending_jobs': pending_jobs,
        'in_progress_jobs': in_progress_jobs,
        'total_cost': total_cost,
        'total_co2': total_co2,
        'recent_jobs': recent_jobs,
    }
    return render(request, 'fabjobs/dashboard.html', context)

@login_required
def get_materials_for_machine(request):
    """API pour récupérer les matériaux compatibles avec une machine"""
    machine_id = request.GET.get('machine')
    if not machine_id:
        return JsonResponse({'error': 'Machine ID required'}, status=400)

    # Récupérer la machine
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Vérifier les permissions
    if not request.user.is_superuser and machine.fablab not in request.user.fablabs.all():
        return JsonResponse({'error': 'Permission denied'}, status=403)

    # Récupérer les matériaux compatibles
    materials = Material.objects.filter(
        machine_types=machine.machine_type,
        fablabs__in=request.user.fablabs.all()
    ).distinct().order_by('name')

    # Formater les données
    materials_data = [{
        'id': str(material.id),  # Convertir en string pour la compatibilité JSON
        'name': f"{material.name} ({material.get_unit_display()})",
        'unit': material.get_unit_display(),
        'price_per_unit': float(material.price_per_unit),
        'co2_per_unit': float(material.co2_per_unit),
        'color': material.color
    } for material in materials]

    return JsonResponse(materials_data, safe=False)

def generate_public_url(machine):
    """Génère une URL publique unique pour une machine"""
    # Utiliser l'ID de la machine et un secret pour générer un hash
    secret = "FabBoardSecret2024"  # À changer en production
    hash_input = f"{machine.id}{secret}".encode()
    return hashlib.sha256(hash_input).hexdigest()[:16]

@csrf_exempt
def public_machine_jobs(request, machine_id, public_hash):
    """Vue publique pour les jobs d'une machine"""
    machine = get_object_or_404(Machine, id=machine_id)
    
    # Vérifier que le hash correspond
    if generate_public_url(machine) != public_hash:
        return JsonResponse({'error': 'Invalid URL'}, status=403)
    
    if request.method == 'POST':
        # Mise à jour du statut d'un job
        job_id = request.POST.get('job_id')
        new_status = request.POST.get('status')
        
        if not job_id or not new_status:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
            
        job = get_object_or_404(Job, id=job_id, machine=machine)
        if new_status in dict(Job.STATUS_CHOICES):
            job.status = new_status
            job.save()
            return redirect('fabjobs:public_machine_jobs', machine_id=machine_id, public_hash=public_hash)
        return JsonResponse({'error': 'Invalid status'}, status=400)
    
    # Récupérer les jobs de la machine
    jobs = Job.objects.filter(machine=machine).order_by('-created_at')
    
    context = {
        'machine': machine,
        'jobs': jobs,
        'status_choices': Job.STATUS_CHOICES,
    }
    return render(request, 'fabjobs/public_machine_jobs.html', context) 