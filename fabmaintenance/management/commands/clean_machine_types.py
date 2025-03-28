from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MaintenanceType

class Command(BaseCommand):
    help = 'Nettoie les types de machines en doublon'

    def handle(self, *args, **kwargs):
        # Trouver les types de machines en doublon
        laser_types = MachineType.objects.filter(name__in=['Découpe Laser', 'Découpe laser'])
        
        if laser_types.count() > 1:
            # Garder celui avec la majuscule
            keep_type = MachineType.objects.get(name='Découpe Laser')
            delete_type = MachineType.objects.get(name='Découpe laser')
            
            # Déplacer les maintenances vers le type à garder
            MaintenanceType.objects.filter(machine_type=delete_type).update(
                machine_type=keep_type
            )
            
            # Supprimer le type en doublon
            delete_type.delete()
            
            self.stdout.write(self.style.SUCCESS('Types de machines nettoyés avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Aucun type de machine en doublon trouvé')) 