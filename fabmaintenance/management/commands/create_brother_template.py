from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MachineTemplate, MaintenanceTemplate
from django.utils import timezone

class Command(BaseCommand):
    help = 'Crée le template de maintenance pour la Brother PR-655'

    def handle(self, *args, **kwargs):
        # Récupérer ou créer le type de machine "Brodeuse"
        machine_type, _ = MachineType.objects.get_or_create(
            name="Brodeuse",
            defaults={
                "description": "Machine à broder industrielle"
            }
        )

        # Créer le template pour la Brother PR-655
        template, _ = MachineTemplate.objects.get_or_create(
            name="Brother PR-655",
            defaults={
                "machine_type": machine_type,
                "manufacturer": "Brother",
                "model": "PR-655",
                "description": """Machine à broder industrielle Brother PR-655
- 6 aiguilles
- Surface de broderie : 300 x 200 mm
- Vitesse max : 1000 points/minute
- Écran LCD tactile
- Système de coupe automatique des fils
- Éclairage LED""",
                "documentation_url": "https://download.brother.com/welcome/doch001119/pr655ug01fr.pdf"
            }
        )

        # Créer les maintenances recommandées
        maintenances = [
            {
                "name": "Nettoyage quotidien",
                "description": "Nettoyage basique de la machine après utilisation",
                "period_days": 1,
                "estimated_duration": timezone.timedelta(minutes=15),
                "priority": 3,
                "instructions": """1. Éteindre la machine et débrancher le cordon d'alimentation
2. Nettoyer la zone du crochet
3. Retirer les peluches et les résidus de fil
4. Nettoyer la surface de la machine avec un chiffon doux
5. Vérifier qu'il n'y a pas de fil coincé dans le mécanisme
6. Vérifier l'état des aiguilles""",
                "required_tools": """- Brosse de nettoyage
- Chiffons doux non pelucheux
- Pinceau fin
- Pince à épiler"""
            },
            {
                "name": "Lubrification",
                "description": "Lubrification des pièces mobiles",
                "period_days": 7,
                "estimated_duration": timezone.timedelta(minutes=30),
                "priority": 3,
                "instructions": """1. Éteindre la machine et débrancher le cordon d'alimentation
2. Retirer la plaque à aiguille
3. Nettoyer la zone du crochet
4. Appliquer une goutte d'huile sur le crochet rotatif
5. Faire tourner le crochet manuellement pour répartir l'huile
6. Remonter la plaque à aiguille
7. Faire fonctionner la machine à vide pendant quelques minutes""",
                "required_tools": """- Huile pour machine à broder
- Tournevis
- Chiffons propres
- Brosse de nettoyage
- Pinceau fin"""
            },
            {
                "name": "Maintenance des aiguilles",
                "description": "Vérification et remplacement des aiguilles",
                "period_days": 30,
                "estimated_duration": timezone.timedelta(minutes=20),
                "priority": 2,
                "instructions": """1. Éteindre la machine
2. Vérifier l'état de chaque aiguille
3. Vérifier l'absence de bavures ou de courbures
4. Remplacer les aiguilles usées ou endommagées
5. Vérifier le bon positionnement des aiguilles
6. Tester chaque aiguille avec un point simple""",
                "required_tools": """- Aiguilles de rechange
- Tournevis pour aiguilles
- Loupe d'inspection
- Tissu test
- Fils de test"""
            },
            {
                "name": "Vérification du système de tension",
                "description": "Contrôle et ajustement des tensions de fil",
                "period_days": 90,
                "estimated_duration": timezone.timedelta(minutes=45),
                "priority": 2,
                "instructions": """1. Vérifier les tensions de fil pour chaque aiguille
2. Nettoyer les disques de tension
3. Vérifier les ressorts de tension
4. Ajuster les tensions si nécessaire
5. Tester avec différents types de fils
6. Vérifier le passage des fils
7. Faire des tests de broderie""",
                "required_tools": """- Jeu de fils de test
- Tissu test
- Tournevis de précision
- Brosse de nettoyage
- Pince à épiler"""
            },
            {
                "name": "Maintenance du système électronique",
                "description": "Vérification des composants électroniques",
                "period_days": 180,
                "estimated_duration": timezone.timedelta(minutes=60),
                "priority": 1,
                "instructions": """1. Vérifier l'écran LCD
2. Tester tous les boutons et commandes
3. Vérifier les capteurs
4. Contrôler les LED d'éclairage
5. Vérifier les messages d'erreur
6. Mettre à jour le logiciel si nécessaire
7. Tester toutes les fonctions""",
                "required_tools": """- Clé USB
- Chiffon antistatique
- Kit de diagnostic Brother
- Documentation technique"""
            },
            {
                "name": "Révision complète",
                "description": "Inspection et maintenance complète de la machine",
                "period_days": 365,
                "estimated_duration": timezone.timedelta(hours=3),
                "priority": 1,
                "instructions": """1. Inspection complète de la machine :
   - Système d'entraînement
   - Système de tension
   - Système de coupe des fils
   - Système électronique
   - Calibration des capteurs
2. Nettoyage approfondi
3. Lubrification complète
4. Test de toutes les fonctions
5. Mise à jour du firmware
6. Tests de broderie complets
7. Vérification des paramètres""",
                "required_tools": """- Kit complet d'outils Brother
- Huile et lubrifiants
- Kit de nettoyage
- Pièces de rechange courantes
- Matériel de test
- Documentation technique
- Logiciel de diagnostic"""
            }
        ]

        # Créer les maintenances
        for maint in maintenances:
            MaintenanceTemplate.objects.create(
                machine_template=template,
                **maint
            )

        self.stdout.write(self.style.SUCCESS('Template Brother PR-655 créé avec succès')) 