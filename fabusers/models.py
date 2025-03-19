from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

class FabLab(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom")
    address = models.CharField(max_length=200, blank=True, null=True)
    users = models.ManyToManyField(User, related_name='fablabs', blank=True)
    admins = models.ManyToManyField(User, related_name='admin_fablabs', blank=True, verbose_name="Administrateurs")
    invitation_token = models.CharField(max_length=100, unique=True, blank=True, null=True, verbose_name="Token d'invitation")
    
    def __str__(self):
        return self.name

    def generate_invitation_token(self):
        """Génère un nouveau token d'invitation unique."""
        import secrets
        token = secrets.token_urlsafe(32)
        self.invitation_token = token
        self.save()
        return token

    def get_invitation_link(self, request=None):
        """Retourne le lien d'invitation complet."""
        if not self.invitation_token:
            self.generate_invitation_token()
        url = reverse('fabusers:register_with_invitation', kwargs={'token': self.invitation_token})
        if request:
            return request.build_absolute_uri(url)
        return url

    class Meta:
        verbose_name = "FabLab"
        verbose_name_plural = "FabLabs"

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    profile_picture = models.ImageField(upload_to='profile_pictures/', blank=True, null=True, verbose_name="Photo de profil")
    accepts_contact = models.BooleanField(default=False, verbose_name="Accepte d'être contacté")
    fablab = models.ForeignKey(FabLab, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="FabLab principal")
    last_activity = models.DateTimeField(auto_now=True, verbose_name="Dernière activité")
    avatar_color = models.CharField(max_length=7, default='#007bff', verbose_name="Couleur de l'avatar")

    def __str__(self):
        return f"Profil de {self.user.username}"

    class Meta:
        verbose_name = "Profil utilisateur"
        verbose_name_plural = "Profils utilisateurs"

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Crée automatiquement un profil utilisateur lors de la création d'un utilisateur."""
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Sauvegarde le profil utilisateur lors de la sauvegarde de l'utilisateur."""
    instance.profile.save()

def get_initials(self):
    """Retourne les initiales de l'utilisateur."""
    if self.first_name and self.last_name:
        return f"{self.first_name[0]}{self.last_name[0]}".upper()
    return self.username[:2].upper()

# Ajout de la méthode get_initials au modèle User
User.add_to_class('get_initials', get_initials)
