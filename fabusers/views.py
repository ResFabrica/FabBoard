from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .forms import UserRegistrationForm
from .models import FabLab
from fabmaintenance.models import Machine, Maintenance
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q, Count
import json
import csv
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.views.decorators.csrf import csrf_exempt

User = get_user_model()

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie !')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()
    return render(request, 'fabusers/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                # Gérer l'option "Se souvenir de moi"
                if request.POST.get('remember'):
                    # Définir la durée de la session à 30 jours
                    request.session.set_expiry(30 * 24 * 60 * 60)
                else:
                    # Session expire à la fermeture du navigateur
                    request.session.set_expiry(0)
                messages.success(request, f'Bienvenue, {username} !')
                return redirect('dashboard')
    else:
        form = AuthenticationForm()
    return render(request, 'fabusers/login.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'fabusers/profile.html', {'user': request.user})

def terms(request):
    return render(request, 'fabusers/terms.html')

@login_required
def fablab_users(request):
    """Vue pour afficher et gérer les utilisateurs par FabLab."""
    # Récupérer le FabLab sélectionné depuis l'URL
    selected_fablab_id = request.GET.get('fablab')
    expand = request.GET.get('expand', 'true') == 'true'
    
    # FabLabs où l'utilisateur est admin
    admin_fablabs = FabLab.objects.filter(admins=request.user).prefetch_related('users', 'admins', 'users__profile')
    
    # Si l'utilisateur est super admin, ajouter les autres FabLabs
    other_fablabs = []
    if request.user.is_superuser:
        other_fablabs = FabLab.objects.exclude(admins=request.user).prefetch_related('users', 'admins', 'users__profile')
    
    # FabLab sélectionné
    selected_fablab = None
    if selected_fablab_id:
        try:
            # Vérifier si l'utilisateur a accès à ce FabLab
            if request.user.is_superuser:
                selected_fablab = FabLab.objects.get(id=selected_fablab_id)
            else:
                selected_fablab = admin_fablabs.get(id=selected_fablab_id)
        except FabLab.DoesNotExist:
            pass
    
    return render(request, 'fabusers/fablab_users.html', {
        'admin_fablabs': admin_fablabs,
        'other_fablabs': other_fablabs,
        'is_superuser': request.user.is_superuser,
        'selected_fablab': selected_fablab,
        'expand': expand
    })

@login_required
def search_users(request):
    """API pour rechercher des utilisateurs."""
    query = request.GET.get('q', '')
    fablab_id = request.GET.get('fablab_id')
    global_search = request.GET.get('global_search', 'false') == 'true'
    
    if not query or len(query) < 2:
        return JsonResponse({'users': []})
    
    # Construire la requête de base
    base_query = Q(username__icontains=query) | \
                Q(first_name__icontains=query) | \
                Q(last_name__icontains=query) | \
                Q(email__icontains=query) | \
                Q(profile__phone__icontains=query)
    
    # Si c'est une recherche globale et que l'utilisateur est admin ou super admin
    if global_search and (request.user.is_superuser or FabLab.objects.filter(admins=request.user).exists()):
        users = User.objects.filter(base_query)
    # Si un fablab_id est spécifié, filtrer par fablab
    elif fablab_id:
        try:
            fablab = FabLab.objects.get(id=fablab_id)
            users = fablab.users.filter(base_query)
        except FabLab.DoesNotExist:
            return JsonResponse({'users': []})
    else:
        # Par défaut, retourner une liste vide
        return JsonResponse({'users': []})
    
    # Limiter les résultats et inclure les relations nécessaires
    users = users.select_related('profile')[:10]
    
    users_data = [{
        'id': user.id,
        'username': user.username,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'phone': user.profile.phone if hasattr(user, 'profile') else None,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'last_activity': user.profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'profile') and user.profile.last_activity else None,
        'avatar_color': user.profile.avatar_color if hasattr(user, 'profile') else '#6c757d'
    } for user in users]
    
    return JsonResponse({'users': users_data})

@login_required
@csrf_exempt
def add_user_to_fablab(request, fablab_id):
    """Ajouter un utilisateur à un FabLab."""
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        
        if not user_id:
            return JsonResponse({
                'status': 'error',
                'message': 'ID utilisateur manquant'
            }, status=400)
        
        # Récupérer le FabLab
        try:
            fablab = FabLab.objects.get(id=fablab_id)
        except FabLab.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'FabLab non trouvé'
            }, status=404)
        
        # Vérifier les permissions
        if not request.user.is_superuser and not request.user in fablab.admins.all():
            return JsonResponse({
                'status': 'error',
                'message': 'Permission refusée'
            }, status=403)
        
        # Récupérer l'utilisateur
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return JsonResponse({
                'status': 'error',
                'message': 'Utilisateur non trouvé'
            }, status=404)
        
        # Ajouter l'utilisateur au FabLab
        fablab.users.add(user)
        
        return JsonResponse({
            'status': 'success',
            'message': f'Utilisateur ajouté au FabLab {fablab.name}'
        })
    except json.JSONDecodeError:
        return JsonResponse({
            'status': 'error',
            'message': 'Données invalides'
        }, status=400)

@login_required
def remove_user_from_fablab(request, fablab_id, user_id):
    """API pour retirer un utilisateur d'un FabLab."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        fablab = FabLab.objects.get(id=fablab_id)
        user = User.objects.get(id=user_id)
        
        fablab.users.remove(user)
        return JsonResponse({'status': 'success'})
    except (FabLab.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'FabLab ou utilisateur non trouvé'}, status=404)

@login_required
def toggle_staff(request, user_id):
    """API pour basculer les droits staff d'un utilisateur."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        user.is_staff = not user.is_staff
        user.save()
        return JsonResponse({
            'status': 'success',
            'is_staff': user.is_staff
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Utilisateur non trouvé'}, status=404)

@login_required
def toggle_admin(request, user_id):
    """API pour basculer les droits admin d'un utilisateur."""
    if not request.user.is_superuser:
        return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        user = User.objects.get(id=user_id)
        # Empêcher un admin de se retirer ses propres droits
        if user == request.user:
            return JsonResponse({
                'status': 'error',
                'message': 'Vous ne pouvez pas modifier vos propres droits admin'
            }, status=400)
        
        user.is_superuser = not user.is_superuser
        # Si l'utilisateur devient admin, il doit aussi être staff
        if user.is_superuser:
            user.is_staff = True
        user.save()
        return JsonResponse({
            'status': 'success',
            'is_superuser': user.is_superuser,
            'is_staff': user.is_staff
        })
    except User.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Utilisateur non trouvé'}, status=404)

@login_required
def toggle_fablab_admin(request, fablab_id, user_id):
    """API pour basculer les droits d'administrateur FabLab."""
    if not (request.user.is_superuser or request.user in FabLab.objects.get(id=fablab_id).admins.all()):
        return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        fablab = FabLab.objects.get(id=fablab_id)
        user = User.objects.get(id=user_id)
        
        if user in fablab.admins.all():
            fablab.admins.remove(user)
            is_admin = False
        else:
            fablab.admins.add(user)
            is_admin = True
        
        return JsonResponse({
            'status': 'success',
            'is_admin': is_admin
        })
    except (FabLab.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'FabLab ou utilisateur non trouvé'}, status=404)

@login_required
def bulk_add_admin(request, fablab_id):
    """API pour ajouter plusieurs utilisateurs comme admin d'un FabLab."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        fablab = FabLab.objects.get(id=fablab_id)
        
        # Vérifier les permissions
        if not (request.user.is_superuser or request.user in fablab.admins.all()):
            return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
        
        users = User.objects.filter(id__in=user_ids)
        fablab.admins.add(*users)
        
        return JsonResponse({
            'status': 'success',
            'message': f'{len(users)} utilisateurs ajoutés comme administrateurs'
        })
    except (FabLab.DoesNotExist, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Données invalides'}, status=400)

@login_required
def bulk_remove_users(request, fablab_id):
    """API pour retirer plusieurs utilisateurs d'un FabLab."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_ids = data.get('user_ids', [])
        fablab = FabLab.objects.get(id=fablab_id)
        
        # Vérifier les permissions
        if not (request.user.is_superuser or request.user in fablab.admins.all()):
            return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
        
        users = User.objects.filter(id__in=user_ids)
        fablab.users.remove(*users)
        # Retirer également les droits d'admin si nécessaire
        fablab.admins.remove(*users)
        
        return JsonResponse({
            'status': 'success',
            'message': f'{len(users)} utilisateurs retirés du FabLab'
        })
    except (FabLab.DoesNotExist, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Données invalides'}, status=400)

@login_required
def update_avatar_color(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            color = data.get('color')
            
            if color and color.startswith('#'):
                request.user.profile.avatar_color = color
                request.user.profile.save()
                return JsonResponse({'status': 'success'})
            
            return JsonResponse({'status': 'error', 'message': 'Couleur invalide'})
            
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Données JSON invalides'})
    
    return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)

@login_required
@csrf_exempt
def fablab_admin(request):
    """Vue pour gérer les FabLabs."""
    # FabLabs où l'utilisateur est admin
    admin_fablabs = FabLab.objects.filter(admins=request.user).prefetch_related('users', 'admins')
    
    # Si l'utilisateur est super admin, ajouter les autres FabLabs
    other_fablabs = []
    if request.user.is_superuser:
        other_fablabs = FabLab.objects.exclude(admins=request.user).prefetch_related('users', 'admins')
    
    # Enrichir les FabLabs avec les informations sur les machines
    for fablab in admin_fablabs:
        fablab.machine_count = Machine.objects.filter(fablab=fablab).count()
        fablab.machines = Machine.objects.filter(fablab=fablab).select_related('machine_type')[:5]  # Limiter à 5 machines pour l'aperçu
    
    for fablab in other_fablabs:
        fablab.machine_count = Machine.objects.filter(fablab=fablab).count()
        fablab.machines = Machine.objects.filter(fablab=fablab).select_related('machine_type')[:5]
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            name = data.get('name')
            address = data.get('address')
            
            if not name:
                return JsonResponse({
                    'success': False,
                    'error': 'Le nom du FabLab est requis'
                }, status=400)
            
            # Vérifier si le nom existe déjà
            if FabLab.objects.filter(name=name).exists():
                return JsonResponse({
                    'success': False,
                    'error': 'Un FabLab avec ce nom existe déjà'
                }, status=400)
            
            # Créer le nouveau FabLab
            fablab = FabLab.objects.create(
                name=name,
                address=address
            )
            
            # Ajouter l'utilisateur comme admin
            fablab.admins.add(request.user)
            
            return JsonResponse({'success': True})
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Données invalides'
            }, status=400)
    
    return render(request, 'fabusers/fablab_admin.html', {
        'admin_fablabs': admin_fablabs,
        'other_fablabs': other_fablabs,
        'is_superuser': request.user.is_superuser,
    })

@login_required
def delete_fablab(request, fablab_id):
    """Vue pour supprimer un FabLab."""
    if not request.user.is_superuser and not request.user.admin_fablabs.filter(id=fablab_id).exists():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        fablab = FabLab.objects.get(id=fablab_id)
        fablab.delete()
        return JsonResponse({'success': True})
    except FabLab.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'FabLab not found'}, status=404)

@login_required
def update_fablab(request, fablab_id):
    """Vue pour mettre à jour les informations d'un FabLab."""
    if not request.user.is_superuser and not request.user.admin_fablabs.filter(id=fablab_id).exists():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        fablab = FabLab.objects.get(id=fablab_id)
        data = json.loads(request.body)
        
        # Vérifier si le nom existe déjà pour un autre FabLab
        if FabLab.objects.exclude(id=fablab_id).filter(name=data.get('name')).exists():
            return JsonResponse({
                'success': False,
                'error': 'Un FabLab avec ce nom existe déjà'
            }, status=400)
        
        fablab.name = data.get('name', fablab.name)
        fablab.address = data.get('address', fablab.address)
        fablab.save()
        
        return JsonResponse({'success': True})
    except FabLab.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'FabLab not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

@login_required
def duplicate_fablab(request, fablab_id):
    """Vue pour dupliquer un FabLab avec ses machines et leurs maintenances."""
    if not request.user.is_superuser and not request.user.admin_fablabs.filter(id=fablab_id).exists():
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)
    
    try:
        original_fablab = FabLab.objects.get(id=fablab_id)
        data = json.loads(request.body)
        new_name = data.get('name', f"{original_fablab.name} (copie)")
        
        # Vérifier si le nom existe déjà
        if FabLab.objects.filter(name=new_name).exists():
            return JsonResponse({
                'success': False,
                'error': 'Un FabLab avec ce nom existe déjà'
            }, status=400)
        
        # Créer une copie du FabLab avec le nouveau nom
        new_fablab = FabLab.objects.create(
            name=new_name,
            address=original_fablab.address
        )
        
        # Copier les utilisateurs et administrateurs
        new_fablab.users.set(original_fablab.users.all())
        new_fablab.admins.set(original_fablab.admins.all())
        
        # Dupliquer les machines si demandé
        if data.get('duplicate_machines', False):
            # Créer un dictionnaire pour mapper les anciennes machines aux nouvelles
            machine_mapping = {}
            
            for machine in original_fablab.machine_set.all():
                # Créer une copie de la machine
                new_machine = Machine.objects.create(
                    name=machine.name,
                    machine_type=machine.machine_type,
                    template=machine.template,
                    fablab=new_fablab,
                    serial_number=f"{machine.serial_number} (copie)" if machine.serial_number else None,
                    image=machine.image if machine.image else None
                )
                machine_mapping[machine.id] = new_machine
                
                # Dupliquer les maintenances de la machine
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
    except FabLab.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'FabLab not found'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid data'}, status=400)

@login_required
def admin_dashboard(request):
    """Vue pour le tableau de bord d'administration."""
    if not request.user.is_superuser and not request.user.admin_fablabs.exists():
        return HttpResponseForbidden("Accès non autorisé")
    
    # Statistiques globales pour les super utilisateurs
    if request.user.is_superuser:
        total_users = User.objects.count()
        total_fablabs = FabLab.objects.count()
        total_admins = User.objects.filter(is_staff=True).count()
        fablabs = FabLab.objects.annotate(
            user_count=Count('users'),
            admin_count=Count('admins')
        ).all()
    else:
        # Statistiques limitées aux FabLabs administrés
        admin_fablabs = request.user.admin_fablabs.all()
        total_users = User.objects.filter(fablabs__in=admin_fablabs).distinct().count()
        total_fablabs = admin_fablabs.count()
        total_admins = User.objects.filter(admin_fablabs__in=admin_fablabs).distinct().count()
        fablabs = admin_fablabs.annotate(
            user_count=Count('users'),
            admin_count=Count('admins')
        )
    
    context = {
        'total_users': total_users,
        'total_fablabs': total_fablabs,
        'total_admins': total_admins,
        'fablabs': fablabs,
        'is_superuser': request.user.is_superuser,
    }
    
    return render(request, 'fabusers/admin_dashboard.html', context)

def register_with_invitation(request, token):
    """Vue pour l'inscription avec un token d'invitation."""
    try:
        fablab = FabLab.objects.get(invitation_token=token)
    except FabLab.DoesNotExist:
        messages.error(request, "Token d'invitation invalide ou expiré.")
        return redirect('home')

    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Ajouter l'utilisateur au FabLab
            fablab.users.add(user)
            # Définir ce FabLab comme FabLab principal de l'utilisateur
            user.profile.fablab = fablab
            user.profile.save()
            
            login(request, user)
            messages.success(request, f'Bienvenue dans {fablab.name} !')
            return redirect('dashboard')
    else:
        form = UserRegistrationForm()

    return render(request, 'fabusers/register.html', {
        'form': form,
        'fablab': fablab,
        'invitation': True
    })
