from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MaintenanceType

class Command(BaseCommand):
    help = 'Initialise les types de machines et de maintenance par défaut'

    def handle(self, *args, **kwargs):
        # Création des types de machines
        printer_3d = MachineType.objects.create(
            name='Imprimante 3D',
            description='Imprimante 3D FDM'
        )
        laser_cutter = MachineType.objects.create(
            name='Découpe Laser',
            description='Machine de découpe laser'
        )

        # Maintenances pour imprimante 3D
        printer_maintenances = [
            ('Nettoyage print core', 'Nettoyage du print core', 30),
            ('Nettoyage plateau', 'Nettoyage du plateau d\'impression', 7),
            ('Lubrification axes', 'Lubrification des axes X et Y', 90),
            ('Calibration plateau', 'Calibration du plateau d\'impression', 30),
            ('Lubrification des axes Z', 'Lubrification des axes Z', 90),
        ]

        for name, desc, freq in printer_maintenances:
            MaintenanceType.objects.create(
                name=name,
                description=desc,
                machine_type=printer_3d,
                period_days=freq
            )

        # Maintenances pour découpe laser
        laser_maintenances = [
            ('Nettoyage de l\'optique', 'Nettoyage des miroirs et de la lentille', 7),
            ('Aspiration sous le plateau', 'Nettoyage sous le plateau de découpe', 7),
            ('Changement préfiltre', 'Remplacement du préfiltre', 30),
            ('Changement du gros filtre', 'Remplacement du filtre principal', 180),
            ('Renouvellement des charbons', 'Remplacement des filtres à charbon', 180),
        ]

        for name, desc, freq in laser_maintenances:
            MaintenanceType.objects.create(
                name=name,
                description=desc,
                machine_type=laser_cutter,
                period_days=freq
            )

        self.stdout.write(self.style.SUCCESS('Types de machines et maintenances créés avec succès')) 