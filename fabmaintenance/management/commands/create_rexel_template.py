from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MachineTemplate, MaintenanceTemplate
from datetime import timedelta

class Command(BaseCommand):
    help = 'Crée le template du destructeur Rexel Momentum X415 avec ses maintenances'

    def handle(self, *args, **kwargs):
        # Créer le type de machine "Destructeur de documents"
        shredder_type, _ = MachineType.objects.get_or_create(
            name="Destructeur de documents",
            defaults={
                "description": "Machine de destruction de documents",
                "icon": "fas fa-shredder",
                "color": "#007bff",
                "default_maintenance_period": 30,
                "requires_certification": False,
                "safety_instructions": """Instructions de sécurité pour les destructeurs de documents :
- Ne jamais insérer de mains ou d'objets métalliques dans la fente d'alimentation
- Ne pas surcharger la machine (max 15 feuilles pour le X415)
- Vider régulièrement la corbeille
- Ne pas utiliser en continu plus de 2 heures
- Laisser refroidir 60 minutes après 2 heures d'utilisation"""
            }
        )

        # Créer le template pour le Rexel Momentum X415
        template, created = MachineTemplate.objects.get_or_create(
            name="Rexel Momentum X415",
            defaults={
                "machine_type": shredder_type,
                "manufacturer": "Rexel",
                "model": "Momentum X415",
                "description": """Destructeur de documents Rexel Momentum X415
- Capacité : 15 feuilles (80g)
- Niveau de sécurité : P-4 (coupe croisée)
- Temps de fonctionnement : 2 heures
- Corbeille : 23 litres
- Technologie anti-bourrage
- Interface tactile
- Opération ultra silencieuse (58 dBA)""",
                "documentation_url": "https://www.rexeleurope.com/product/document/62307/pdf"
            }
        )

        if created:
            # Créer les maintenances par défaut
            maintenances = [
                {
                    "name": "Nettoyage de la corbeille",
                    "description": "Vider et nettoyer la corbeille de 23 litres",
                    "period_days": 7,
                    "estimated_duration": timedelta(minutes=5),
                    "priority": 2,
                    "instructions": "1. Éteindre la machine\n2. Vider la corbeille\n3. Nettoyer les résidus de papier\n4. Remettre la corbeille en place",
                    "required_tools": "Chiffon, aspirateur"
                },
                {
                    "name": "Nettoyage des lames",
                    "description": "Nettoyage des lames de coupe",
                    "period_days": 30,
                    "estimated_duration": timedelta(minutes=15),
                    "priority": 3,
                    "instructions": "1. Éteindre et débrancher la machine\n2. Ouvrir le capot\n3. Nettoyer les lames avec un chiffon sec\n4. Vérifier l'état des lames\n5. Refermer le capot",
                    "required_tools": "Chiffon sec, tournevis"
                },
                {
                    "name": "Lubrification des lames",
                    "description": "Lubrification des lames de coupe",
                    "period_days": 90,
                    "estimated_duration": timedelta(minutes=20),
                    "priority": 3,
                    "instructions": "1. Éteindre et débrancher la machine\n2. Ouvrir le capot\n3. Appliquer l'huile de lubrification sur les lames\n4. Faire tourner les lames manuellement\n5. Refermer le capot",
                    "required_tools": "Huile de lubrification pour destructeur, chiffon"
                },
                {
                    "name": "Vérification générale",
                    "description": "Vérification générale de la machine",
                    "period_days": 180,
                    "estimated_duration": timedelta(minutes=30),
                    "priority": 2,
                    "instructions": "1. Vérifier l'état général de la machine\n2. Tester la fonction anti-bourrage\n3. Vérifier le niveau sonore\n4. Tester la capacité maximale\n5. Nettoyer l'extérieur de la machine",
                    "required_tools": "Chiffon, aspirateur, papier test"
                }
            ]

            for maintenance in maintenances:
                MaintenanceTemplate.objects.create(
                    machine_template=template,
                    **maintenance
                )

            self.stdout.write(self.style.SUCCESS('Template Rexel Momentum X415 créé avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Le template Rexel Momentum X415 existe déjà')) 