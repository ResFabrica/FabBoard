from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from fabmaintenance.models import FabLab

class Command(BaseCommand):
    help = 'Associe l\'utilisateur bdenaeyer au FabLab FabStudio'

    def handle(self, *args, **kwargs):
        try:
            user = User.objects.get(username='bdenaeyer')
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR('L\'utilisateur bdenaeyer n\'existe pas'))
            return

        fabstudio, created = FabLab.objects.get_or_create(
            name='FabStudio',
            defaults={'address': 'Adresse du FabStudio'}
        )

        if created:
            self.stdout.write(self.style.SUCCESS('FabLab FabStudio créé'))

        fabstudio.users.add(user)
        self.stdout.write(
            self.style.SUCCESS(f'Utilisateur {user.username} associé au FabLab {fabstudio.name}')
        ) 