from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MachineTemplate, MaintenanceTemplate
from datetime import timedelta

class Command(BaseCommand):
    help = 'Crée le template de la machine Beambox Pro avec ses maintenances'

    def handle(self, *args, **kwargs):
        # Récupérer le type de machine "Découpe Laser"
        laser_type = MachineType.objects.get(name='Découpe Laser')

        # Créer le template de la Beambox Pro
        beambox_template, created = MachineTemplate.objects.get_or_create(
            name='Beambox Pro',
            defaults={
                'machine_type': laser_type,
                'manufacturer': 'FLUX',
                'model': 'Beambox Pro',
                'description': """Machine de découpe laser FLUX Beambox Pro.
                
Caractéristiques principales :
- Zone de travail : 400 x 300 mm
- Puissance laser : 40W
- Système de ventilation intégré
- Système de refroidissement à eau
- Interface tactile""",
                'documentation_url': 'https://support.flux3dp.com/hc/fr-fr/sections/360000275375-IV-Maintenance'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Template Beambox Pro créé avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Le template Beambox Pro existe déjà'))
            return

        # Créer les maintenances recommandées
        maintenances = [
            {
                'name': 'Nettoyage quotidien',
                'description': 'Nettoyage de base de la machine et de la zone de travail.',
                'period_days': 1,
                'estimated_duration': timedelta(minutes=10),
                'priority': 2,
                'instructions': """1. Nettoyer la table de travail avec un aspirateur
2. Vérifier et vider le bac de récupération des déchets
3. Nettoyer la vitre de protection
4. Vérifier que la ventilation fonctionne correctement
5. Nettoyer la zone autour de la machine
6. Vérifier le niveau d'eau dans le réservoir""",
                'required_tools': '- Aspirateur\n- Chiffon non pelucheux\n- Alcool isopropylique\n- Eau distillée'
            },
            {
                'name': 'Nettoyage de l\'optique',
                'description': 'Nettoyage complet du système optique (miroirs et lentille).',
                'period_days': 7,
                'estimated_duration': timedelta(minutes=30),
                'priority': 3,
                'instructions': """1. Retirer le capot de protection
2. Nettoyer les miroirs avec de l'alcool isopropylique et un chiffon non pelucheux
3. Nettoyer la lentille de focalisation
4. Vérifier l'alignement du laser
5. Remettre le capot de protection
6. Tester la puissance du laser""",
                'required_tools': '- Alcool isopropylique\n- Chiffons non pelucheux\n- Kit de nettoyage optique FLUX\n- Multimètre'
            },
            {
                'name': 'Maintenance du système de ventilation',
                'description': 'Nettoyage et vérification du système de ventilation.',
                'period_days': 30,
                'estimated_duration': timedelta(minutes=45),
                'priority': 2,
                'instructions': """1. Vérifier le niveau de remplissage du filtre à charbon actif
2. Nettoyer le préfiltre
3. Vérifier le fonctionnement du ventilateur
4. Nettoyer les conduits d'aspiration
5. Vérifier les connexions des tuyaux
6. Tester le système d'extraction""",
                'required_tools': '- Kit de nettoyage ventilation\n- Filtres de rechange\n- Chiffons\n- Multimètre'
            },
            {
                'name': 'Maintenance du système de refroidissement',
                'description': 'Vérification et maintenance du système de refroidissement à eau.',
                'period_days': 90,
                'estimated_duration': timedelta(minutes=60),
                'priority': 3,
                'instructions': """1. Vérifier le niveau d'eau dans le réservoir
2. Nettoyer le filtre du système de refroidissement
3. Vérifier la température de l'eau
4. Nettoyer les conduits d'eau
5. Vérifier les connexions et les fuites potentielles
6. Remplacer l'eau si nécessaire
7. Vérifier le fonctionnement de la pompe""",
                'required_tools': '- Kit de maintenance refroidissement\n- Eau distillée\n- Chiffons\n- Thermomètre\n- Multimètre'
            },
            {
                'name': 'Remplacement des filtres',
                'description': 'Remplacement des filtres principaux et à charbon actif.',
                'period_days': 180,
                'estimated_duration': timedelta(minutes=30),
                'priority': 2,
                'instructions': """1. Retirer les anciens filtres
2. Nettoyer le compartiment des filtres
3. Installer les nouveaux filtres
4. Vérifier l'étanchéité
5. Tester le système de ventilation
6. Vérifier la pression d'air""",
                'required_tools': '- Filtres de rechange FLUX\n- Kit de nettoyage\n- Chiffons\n- Manomètre'
            },
            {
                'name': 'Vérification générale',
                'description': 'Vérification complète de la machine et de ses composants.',
                'period_days': 365,
                'estimated_duration': timedelta(hours=2),
                'priority': 4,
                'instructions': """1. Vérifier tous les composants mécaniques
2. Tester le système de sécurité
3. Vérifier l'alignement du laser
4. Tester la précision de la machine
5. Vérifier les paramètres de puissance
6. Nettoyer et lubrifier les rails
7. Vérifier les connexions électriques
8. Tester le système d'urgence
9. Vérifier les paramètres de la carte mère
10. Mettre à jour le firmware si nécessaire""",
                'required_tools': '- Kit de maintenance complet\n- Multimètre\n- Outils de précision\n- Lubrifiants\n- Oscilloscope\n- Kit de diagnostic FLUX'
            }
        ]

        # Créer les maintenances
        for maint in maintenances:
            MaintenanceTemplate.objects.create(
                machine_template=beambox_template,
                **maint
            )

        self.stdout.write(self.style.SUCCESS(f'{len(maintenances)} maintenances créées avec succès')) 