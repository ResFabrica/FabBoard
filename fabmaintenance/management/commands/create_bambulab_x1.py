from django.core.management.base import BaseCommand
from fabmaintenance.models import MachineType, MachineTemplate, MaintenanceTemplate
from datetime import timedelta

class Command(BaseCommand):
    help = 'Crée le template de la Bambu Lab X1 avec ses maintenances'

    def handle(self, *args, **kwargs):
        # Récupérer le type de machine "Imprimante 3D FDM"
        printer_type = MachineType.objects.get(name='Imprimante 3D FDM')

        # Créer le template de la Bambu Lab X1
        x1_template, created = MachineTemplate.objects.get_or_create(
            name='Bambu Lab X1',
            defaults={
                'machine_type': printer_type,
                'manufacturer': 'Bambu Lab',
                'model': 'X1',
                'description': """Imprimante 3D haute performance avec système de changement automatique de filament (AMS).
                
Caractéristiques principales :
- Impression multi-matériaux avec AMS
- Vitesse d'impression jusqu'à 500 mm/s
- Volume d'impression : 256 x 256 x 256 mm
- Extrudeur à entraînement direct
- Calibration automatique avec Micro Lidar
- Caméra de surveillance intégrée""",
                'documentation_url': 'https://wiki.bambulab.com/en/x1/maintenance/basic-maintenance'
            }
        )

        if created:
            self.stdout.write(self.style.SUCCESS('Template Bambu Lab X1 créé avec succès'))
        else:
            self.stdout.write(self.style.WARNING('Le template Bambu Lab X1 existe déjà'))
            return

        # Créer les maintenances recommandées
        maintenances = [
            {
                'name': 'Nettoyage des tiges en carbone axe X',
                'description': 'Nettoyage des tiges en carbone de l\'axe X pour éliminer la poussière et les débris.',
                'period_days': 30,
                'estimated_duration': timedelta(minutes=15),
                'priority': 2,
                'instructions': """1. Utiliser de l'alcool isopropylique et un chiffon non pelucheux
2. Vaporiser un peu d'alcool sur le tissu
3. Frotter doucement les tiges en carbone pour nettoyer les débris
4. NE PAS utiliser de graisse sur les tiges en carbone""",
                'required_tools': '- Alcool isopropylique\n- Chiffon non pelucheux'
            },
            {
                'name': 'Graissage des vis de l\'axe Z',
                'description': 'Graissage des trois vis de l\'axe Z pour assurer un mouvement fluide.',
                'period_days': 90,
                'estimated_duration': timedelta(minutes=30),
                'priority': 3,
                'instructions': """1. Nettoyer les vis de l'axe Z de toute poussière ou particule
2. Appliquer une fine couche de graisse lubrifiante
3. Déplacer le plateau vers une position basse
4. Appliquer une autre fine couche de graisse
5. Retourner en position initiale
6. Répéter le mouvement plusieurs fois pour répartir la graisse
7. Nettoyer l'excès de graisse près des écrous""",
                'required_tools': '- Graisse lubrifiante (Super Lube 92003 ou Lucas Oil 10533)\n- Chiffon propre'
            },
            {
                'name': 'Nettoyage et maintenance des tiges linéaires',
                'description': 'Nettoyage et maintenance anti-rouille des tiges linéaires des axes Y et Z.',
                'period_days': 30,
                'estimated_duration': timedelta(minutes=20),
                'priority': 2,
                'instructions': """1. Nettoyer les tiges avec de l'alcool isopropylique et un chiffon non pelucheux
2. Vaporiser de l'alcool sur le chiffon et frotter doucement les tiges
3. Appliquer de l'huile anti-rouille avec un chiffon propre
4. En cas de bruit anormal des roulements, appliquer un peu de graisse""",
                'required_tools': '- Alcool isopropylique\n- Chiffons non pelucheux\n- Huile anti-rouille (Super Lube 52004)\n- Graisse (optionnel)'
            },
            {
                'name': 'Nettoyage de l\'extrudeur',
                'description': 'Nettoyage de l\'ensemble de l\'extrudeur pour éliminer la poussière de filament.',
                'period_days': 7,
                'estimated_duration': timedelta(minutes=10),
                'priority': 2,
                'instructions': """1. Vérifier la présence de poussière sur l'engrenage jaune
2. Utiliser de l'air comprimé pour nettoyer l'engrenage
3. Retirer la buse et souffler de l'air comprimé sous l'extrudeur
4. Vérifier l'usure de l'engrenage et le remplacer si nécessaire""",
                'required_tools': '- Air comprimé\n- Gants de protection'
            },
            {
                'name': 'Nettoyage de la buse',
                'description': 'Nettoyage complet de la buse et de l\'intérieur du hotend.',
                'period_days': 30,
                'estimated_duration': timedelta(minutes=45),
                'priority': 3,
                'instructions': """1. Retirer le couvercle avant de l'extrudeur
2. Démonter la chaussette en silicone
3. Chauffer la buse à 200°C
4. Porter des gants résistants à la chaleur
5. Nettoyer la surface de la buse avec un tissu ou une pince
6. Effectuer plusieurs "cold pulls" pour nettoyer l'intérieur
7. Vérifier que la buse est droite et non endommagée""",
                'required_tools': '- Gants résistants à la chaleur\n- Tissu ou pinces\n- Filament pour cold pull'
            },
            {
                'name': 'Nettoyage du Micro Lidar',
                'description': 'Nettoyage de la caméra et du laser du Micro Lidar.',
                'period_days': 3,
                'estimated_duration': timedelta(minutes=5),
                'priority': 3,
                'instructions': """1. Utiliser un chiffon en microfibre et de l'alcool isopropylique
2. Nettoyer doucement la caméra du Micro Lidar
3. Un coton-tige peut être utilisé pour un accès plus facile""",
                'required_tools': '- Chiffon en microfibre\n- Alcool isopropylique\n- Coton-tiges'
            },
            {
                'name': 'Vérification du coupe-filament',
                'description': 'Vérification et remplacement si nécessaire de la lame du coupe-filament.',
                'period_days': 30,
                'estimated_duration': timedelta(minutes=15),
                'priority': 2,
                'instructions': """1. Vérifier l'état de la lame après 3-5 rouleaux de filament standard
2. Pour les filaments abrasifs, vérifier après 1-2 rouleaux
3. Remplacer la lame si elle est émoussée
4. La lame doit être remplacée après environ 5000-7000 coupes""",
                'required_tools': '- Lame de rechange si nécessaire'
            },
            {
                'name': 'Remplacement de la chaussette silicone',
                'description': 'Vérification et remplacement de la chaussette silicone du hotend.',
                'period_days': 60,
                'estimated_duration': timedelta(minutes=10),
                'priority': 2,
                'instructions': """1. Vérifier les signes d'usure sur la chaussette silicone
2. Vérifier que la chaussette reste bien fixée au hotend
3. Si nécessaire, retirer l'ancienne chaussette
4. Installer une nouvelle chaussette""",
                'required_tools': '- Chaussette silicone de rechange'
            },
            {
                'name': 'Lubrification des poulies',
                'description': 'Lubrification des poulies pour éviter les bruits de grincement.',
                'period_days': 90,
                'estimated_duration': timedelta(minutes=15),
                'priority': 1,
                'instructions': """1. Vérifier la présence de bruits de grincement pendant l'impression
2. Appliquer une petite quantité d'huile lubrifiante entre la bride de la poulie et le support en plastique
3. Ne pas ajouter d'huile si aucun bruit n'est présent""",
                'required_tools': '- Huile lubrifiante (Super Lube 52004)'
            },
            {
                'name': 'Nettoyage de la caméra',
                'description': 'Nettoyage de la lentille de la caméra de surveillance.',
                'period_days': 7,
                'estimated_duration': timedelta(minutes=5),
                'priority': 1,
                'instructions': """1. Utiliser un chiffon en microfibre et de l'alcool isopropylique
2. Nettoyer doucement la lentille de la caméra
3. Un coton-tige peut être utilisé pour un accès plus facile""",
                'required_tools': '- Chiffon en microfibre\n- Alcool isopropylique\n- Coton-tiges'
            },
            {
                'name': 'Nettoyage des ventilateurs',
                'description': 'Nettoyage des trois ventilateurs : hotend, couvercle avant et auxiliaire.',
                'period_days': 7,
                'estimated_duration': timedelta(minutes=10),
                'priority': 2,
                'instructions': """1. Éteindre l'imprimante
2. Maintenir les pales des ventilateurs en place
3. Utiliser de l'air comprimé pour nettoyer les pales
4. Vérifier qu'il n'y a plus de poussière ou de débris""",
                'required_tools': '- Air comprimé'
            },
            {
                'name': 'Vérification du nettoyeur de buse',
                'description': 'Vérification et remplacement si nécessaire du nettoyeur de buse.',
                'period_days': 1,
                'estimated_duration': timedelta(minutes=5),
                'priority': 2,
                'instructions': """1. Vérifier avant chaque impression
2. S'assurer qu'il n'y a pas de débris de filament
3. Vérifier que le côté PTFE n'est pas endommagé
4. Vérifier que le nettoyeur reste en position horizontale
5. Remplacer si nécessaire""",
                'required_tools': '- Nettoyeur de buse de rechange si nécessaire'
            },
            {
                'name': 'Remplacement du filtre à charbon actif',
                'description': 'Remplacement du filtre à charbon actif pour la filtration des particules.',
                'period_days': 90,
                'estimated_duration': timedelta(minutes=5),
                'priority': 1,
                'instructions': """1. Retirer l'ancien filtre
2. Installer le nouveau filtre
3. Pour une utilisation intensive (>8h/jour), remplacer tous les mois""",
                'required_tools': '- Filtre à charbon actif de rechange'
            }
        ]

        # Créer les maintenances
        for maint in maintenances:
            MaintenanceTemplate.objects.create(
                machine_template=x1_template,
                **maint
            )

        self.stdout.write(self.style.SUCCESS(f'{len(maintenances)} maintenances créées avec succès')) 