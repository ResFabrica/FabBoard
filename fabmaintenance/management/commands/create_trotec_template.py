from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MachineTemplate, MaintenanceTemplate
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crée le template de maintenance pour la Trotec Speedy'

    def handle(self, *args, **kwargs):
        # Récupérer le type de machine "Découpe Laser"
        machine_type, _ = MachineType.objects.get_or_create(
            name="Découpe Laser",
            defaults={
                "description": "Machine de découpe et gravure laser"
            }
        )

        # Créer le template pour la Trotec Speedy
        template, _ = MachineTemplate.objects.get_or_create(
            name="Trotec Speedy",
            defaults={
                "machine_type": machine_type,
                "manufacturer": "Trotec",
                "model": "Speedy",
                "description": """Découpeuse laser Trotec Speedy
- Surface de travail : 726 x 432 mm
- Puissance : 60W
- Vitesse max : 3,55 m/s
- Système de refroidissement à eau""",
                "documentation_url": "https://www.troteclaser.com/fr/assistance/manuels-dutilisation"
            }
        )

        # Créer les maintenances recommandées
        maintenances = [
            {
                "name": "Nettoyage quotidien",
                "description": "Nettoyage basique de la machine après utilisation",
                "period_days": 1,
                "estimated_duration": timezone.timedelta(minutes=10),
                "priority": 3,
                "instructions": """1. Éteindre la machine et la laisser refroidir
2. Nettoyer la table de découpe avec un aspirateur
3. Essuyer les rails de guidage avec un chiffon sec
4. Vérifier qu'il n'y a pas de débris dans la machine
5. Nettoyer la vitre de protection avec un chiffon doux""",
                "required_tools": """- Aspirateur
- Chiffons doux non pelucheux
- Gants de protection"""
            },
            {
                "name": "Nettoyage des optiques",
                "description": "Nettoyage des miroirs et de la lentille",
                "period_days": 7,
                "estimated_duration": timezone.timedelta(minutes=30),
                "priority": 3,
                "instructions": """1. Éteindre la machine et la laisser refroidir
2. Retirer la lentille de focalisation
3. Nettoyer la lentille avec une lingette optique et du nettoyant pour optiques
4. Inspecter les miroirs
5. Nettoyer les miroirs avec une lingette optique si nécessaire
6. Remonter la lentille
7. Vérifier l'alignement du laser""",
                "required_tools": """- Lingettes optiques
- Nettoyant pour optiques
- Gants non poudrés
- Pinceau doux
- Lampe torche"""
            },
            {
                "name": "Maintenance du système de ventilation",
                "description": "Nettoyage et vérification du système de ventilation",
                "period_days": 30,
                "estimated_duration": timezone.timedelta(minutes=30),
                "priority": 2,
                "instructions": """1. Éteindre la machine et débrancher l'extracteur
2. Vérifier l'état des conduits de ventilation
3. Nettoyer ou remplacer les filtres si nécessaire
4. Vérifier le bon fonctionnement de l'extracteur
5. Vérifier l'étanchéité des connexions
6. Tester le système en marche""",
                "required_tools": """- Aspirateur
- Filtres de rechange
- Gants de protection
- Tournevis
- Chiffons"""
            },
            {
                "name": "Maintenance du système de refroidissement",
                "description": "Vérification du système de refroidissement à eau",
                "period_days": 90,
                "estimated_duration": timezone.timedelta(minutes=45),
                "priority": 2,
                "instructions": """1. Éteindre la machine
2. Vérifier le niveau d'eau du refroidisseur
3. Vérifier la propreté de l'eau
4. Vérifier les connexions des tuyaux
5. Vérifier la température de fonctionnement
6. Remplacer l'eau si nécessaire
7. Tester le système""",
                "required_tools": """- Eau distillée
- Gants de protection
- Entonnoir
- Récipient pour vidange
- Thermomètre"""
            },
            {
                "name": "Remplacement des filtres",
                "description": "Remplacement des filtres d'extraction",
                "period_days": 180,
                "estimated_duration": timezone.timedelta(minutes=30),
                "priority": 2,
                "instructions": """1. Éteindre la machine et l'extracteur
2. Retirer les anciens filtres
3. Nettoyer le compartiment des filtres
4. Installer les nouveaux filtres
5. Vérifier l'étanchéité
6. Tester le système d'extraction""",
                "required_tools": """- Nouveaux filtres
- Gants de protection
- Aspirateur
- Chiffons
- Sac poubelle pour les filtres usagés"""
            },
            {
                "name": "Vérification générale",
                "description": "Inspection complète de la machine",
                "period_days": 365,
                "estimated_duration": timezone.timedelta(hours=2),
                "priority": 1,
                "instructions": """1. Vérification complète des systèmes :
   - Système optique
   - Système de refroidissement
   - Système de ventilation
   - Rails et courroies
   - Connexions électriques
2. Test de tous les systèmes de sécurité
3. Calibration si nécessaire
4. Test de découpe
5. Mise à jour du journal de maintenance""",
                "required_tools": """- Kit complet d'outils
- Matériel de test
- Matériaux pour test de découpe
- Journal de maintenance
- Appareil photo pour documentation"""
            }
        ]

        # Créer les maintenances
        for maint in maintenances:
            MaintenanceTemplate.objects.create(
                machine_template=template,
                **maint
            )

        self.stdout.write(self.style.SUCCESS('Template Trotec créé avec succès')) 