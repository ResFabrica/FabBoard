from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UserRegistrationForm, InvitationRegistrationForm
from .models import FabLab
from django.http import JsonResponse
from django.contrib.auth import get_user_model
from django.db.models import Q
import json
import csv
from django.http import HttpResponse, HttpResponseForbidden, HttpResponseNotFound
from django.urls import reverse

User = get_user_model()

# Create your views here.

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Inscription réussie !')
            return redirect('home')
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
                messages.success(request, f'Bienvenue, {username} !')
                return redirect('home')
            else:
                messages.error(request, 'Nom d\'utilisateur ou mot de passe invalide.')
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
    # FabLabs où l'utilisateur est admin
    admin_fablabs = FabLab.objects.filter(admins=request.user).prefetch_related('users', 'admins', 'users__profile')
    
    # Si l'utilisateur est super admin, ajouter les autres FabLabs
    other_fablabs = []
    if request.user.is_superuser:
        other_fablabs = FabLab.objects.exclude(admins=request.user).prefetch_related('users', 'admins', 'users__profile')
    
    return render(request, 'fabusers/fablab_users.html', {
        'admin_fablabs': admin_fablabs,
        'other_fablabs': other_fablabs,
        'is_superuser': request.user.is_superuser
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
        'full_name': user.get_full_name(),
        'email': user.email,
        'phone': user.profile.phone if hasattr(user, 'profile') else None,
        'is_staff': user.is_staff,
        'is_superuser': user.is_superuser,
        'last_activity': user.profile.last_activity.strftime('%Y-%m-%d %H:%M:%S') if hasattr(user, 'profile') and user.profile.last_activity else None
    } for user in users]
    
    return JsonResponse({'users': users_data})

@login_required
def add_user_to_fablab(request, fablab_id):
    """API pour ajouter un utilisateur à un FabLab."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        user_id = data.get('user_id')
        fablab = FabLab.objects.get(id=fablab_id)
        user = User.objects.get(id=user_id)
        
        fablab.users.add(user)
        return JsonResponse({'status': 'success'})
    except (FabLab.DoesNotExist, User.DoesNotExist):
        return JsonResponse({'status': 'error', 'message': 'FabLab ou utilisateur non trouvé'}, status=404)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Données invalides'}, status=400)

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

def register_with_invitation(request, token):
    """Vue pour l'inscription avec un token d'invitation."""
    fablab = get_object_or_404(FabLab, invitation_token=token)
    
    if request.method == 'POST':
        form = InvitationRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            fablab.users.add(user)
            user.profile.fablab = fablab  # Définir comme FabLab principal
            user.profile.save()
            login(request, user)
            messages.success(request, f'Inscription réussie ! Vous êtes maintenant membre de {fablab.name}')
            return redirect('home')
    else:
        form = InvitationRegistrationForm()
    
    return render(request, 'fabusers/register.html', {
        'form': form,
        'fablab': fablab,
        'invitation': True
    })

@login_required
def generate_invitation_link(request, fablab_id):
    """API pour générer un nouveau lien d'invitation."""
    if not request.user.is_superuser and not request.user.admin_fablabs.filter(id=fablab_id).exists():
        return JsonResponse({'status': 'error', 'message': 'Permission refusée'}, status=403)
    
    fablab = get_object_or_404(FabLab, id=fablab_id)
    token = fablab.generate_invitation_token()
    url = reverse('fabusers:register_with_invitation', kwargs={'token': token})
    invitation_link = request.build_absolute_uri(url)
    
    return JsonResponse({
        'status': 'success',
        'invitation_link': invitation_link
    })
