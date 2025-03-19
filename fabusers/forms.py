from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import FabLab

class UserRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')
    email = forms.EmailField(required=True)
    fablab_name = forms.CharField(max_length=100, required=True, label='Nom de votre FabLab')
    accepts_contact = forms.BooleanField(required=False, label='J\'accepte d\'être contacté par Res Fabrica')
    accepts_terms = forms.BooleanField(required=True, label='J\'accepte les conditions générales d\'utilisation')
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'fablab_name', 'accepts_terms', 'accepts_contact')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Utiliser l'email comme nom d'utilisateur
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Mise à jour du profil utilisateur
            user.profile.accepts_contact = self.cleaned_data['accepts_contact']
            user.profile.save()
            
            # Création du FabLab
            fablab = FabLab.objects.create(name=self.cleaned_data['fablab_name'])
            fablab.users.add(user)
            fablab.admins.add(user)  # L'utilisateur devient admin de son FabLab
        
        return user

class InvitationRegistrationForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, label='Prénom')
    last_name = forms.CharField(max_length=30, required=True, label='Nom')
    email = forms.EmailField(required=True)
    accepts_contact = forms.BooleanField(required=False, label='J\'accepte d\'être contacté par Res Fabrica')
    accepts_terms = forms.BooleanField(required=True, label='J\'accepte les conditions générales d\'utilisation')
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'accepts_terms', 'accepts_contact')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = self.cleaned_data['email']  # Utiliser l'email comme nom d'utilisateur
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        
        if commit:
            user.save()
            # Mise à jour du profil utilisateur
            user.profile.accepts_contact = self.cleaned_data['accepts_contact']
            user.profile.save()
        
        return user 