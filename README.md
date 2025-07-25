# FabBoard

FabBoard est une application web Django pour la gestion de FabLabs, permettant de suivre les projets, les tâches, la maintenance des machines, et de planifier les événements.

## Fonctionnalités

### ✅ Fonctionnalités Principales (Stables)

- **Gestion des utilisateurs et des FabLabs**
  - Authentification sécurisée
  - Gestion multi-FabLabs avec isolation des données
  - Rôles et permissions par FabLab

- **Gestion des projets avec système de vues personnalisables**
  - Création de vues personnalisées par FabLab
  - Sections organisées avec drag & drop
  - Système de tags pour l'organisation
  - Champs personnalisés pour les tâches

- **Suivi des tâches avancé**
  - Assignation d'utilisateurs et dates limites
  - Assignation multiple d'une tâche à plusieurs sections
  - Système de tags pour l'organisation
  - Champs personnalisés configurables
  - Gestion des fichiers attachés
  - Interface responsive avec drag & drop

- **Gestion de la maintenance des machines**
  - Catalogue de machines avec templates
  - Planification de maintenances récurrentes
  - Types de maintenance prédéfinis par type de machine
  - Accès public pour les interventions externes
  - Historique complet des interventions

### 🔄 Fonctionnalités en Développement

- **📅 Module Calendrier** *(En développement)*
  - Calendrier interactif pour visualiser tous les événements
  - Événements liés aux tâches, maintenances et événements personnalisés
  - Filtrage par FabLab
  - Événements sur toute la journée ou avec horaires précis
  - Assignation d'utilisateurs aux événements
  - Interface FullCalendar intégrée

- **🛠️ Module Jobs de Fabrication** *(En développement)*
  - Gestion des jobs de fabrication (impression 3D, découpe laser, etc.)
  - Catalogue de matériaux avec prix et impact CO2
  - Calcul automatique des coûts (matière + énergie)
  - Suivi des émissions CO2 par job
  - Gestion des fichiers (STL, GCODE, résultats)
  - Statuts de progression (En attente, En cours, Terminé, etc.)
  - Interface publique pour les utilisateurs externes
  - Estimation et suivi des durées réelles

## Prérequis

- Python 3.8 ou supérieur
- pip (gestionnaire de paquets Python)
- Navigateur web moderne

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/ResFabrica/FabBoard.git
cd FabBoard
```

2. Créez un environnement virtuel et activez-le :
```bash
python -m venv venv
source venv/bin/activate  # Sur Linux/Mac
# ou
venv\Scripts\activate  # Sur Windows
```

3. Installez les dépendances :
```bash
pip install -r requirements.txt
```

4. Effectuez les migrations de la base de données :
```bash
python manage.py migrate
```

5. Créez un superutilisateur :
```bash
python manage.py createsuperuser
```

6. Lancez le serveur de développement :
```bash
python manage.py runserver
```

L'application sera accessible à l'adresse http://localhost:8000

## Structure du projet

- `fabusers/` : Gestion des utilisateurs et des FabLabs
- `fabprojects/` : Gestion des projets et des tâches
- `fabmaintenance/` : Gestion de la maintenance des machines
- `fabcalendar/` : Gestion des événements et du calendrier *(En développement)*
- `fabjobs/` : Gestion des jobs de fabrication *(En développement)*
- `static/` : Fichiers statiques (CSS, JavaScript, images)
- `media/` : Fichiers uploadés par les utilisateurs
- `templates/` : Templates HTML

## Configuration

Les paramètres principaux se trouvent dans `FabBoard/settings.py`. Pour la production, assurez-vous de :

- Définir `DEBUG = False`
- Configurer une base de données appropriée
- Configurer correctement `ALLOWED_HOSTS`
- Utiliser des paramètres de sécurité appropriés

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. Fork le projet
2. Créer une branche pour votre fonctionnalité
3. Commiter vos changements
4. Pousser vers la branche
5. Créer une Pull Request

## Licence

Ce projet est sous licence GNU GPL v3 - voir le fichier [LICENSE](LICENSE) pour plus de détails.

## Support

Pour toute question ou problème, veuillez ouvrir une issue sur GitHub.

## 🔧 Présentation

FabBoard est une application web open-source conçue pour simplifier la gestion complète des FabLabs. Développée avec Django, elle offre une interface intuitive permettant aux équipes de gérer leurs projets, tâches, maintenances et planifier leurs activités.

## ✨ Fonctionnalités Principales

- **Gestion Multi-FabLabs**
  - Chaque FabLab gère son propre parc de machines et projets
  - Interface dédiée par FabLab
  - Collaboration entre membres d'un même FabLab

- **Gestion des Projets & Tâches**
  - Vues personnalisables avec sections organisées
  - Drag & drop pour réorganiser les tâches
  - Assignation multiple des tâches à plusieurs sections
  - Système de tags et champs personnalisés
  - Gestion des fichiers attachés

- **Gestion des Machines & Maintenance**
  - Catalogue de machines avec photos et caractéristiques
  - Types de machines prédéfinis (Imprimantes 3D, Découpeuses Laser, etc.)
  - Planification de maintenances récurrentes
  - Accès public pour les interventions externes

- **Interface Moderne**
  - Design responsive et intuitif
  - Drag & drop avec threshold pour éviter les conflits
  - Recherche en temps réel
  - Notifications et alertes

## 🚀 Démo

Vous souhaitez tester FabBoard ?

1. Rendez-vous sur [maintenance.resfabrica.fr](https://maintenance.resfabrica.fr)
2. Créez un compte avec votre email
3. Ajoutez votre premier FabLab
4. Commencez à gérer vos projets et machines !

## 💡 Cas d'Usage

- **FabLabs** : Gestion complète des projets et du parc machines
- **Makerspaces** : Organisation des projets et suivi des maintenances
- **Ateliers Partagés** : Coordination des activités et interventions
- **Écoles & Universités** : Gestion des projets pédagogiques et équipements

## 🔒 Sécurité & Confidentialité

- Authentification sécurisée
- Données isolées par FabLab
- Accès contrôlé aux fonctionnalités
- Conformité RGPD

## 🤝 Contribution

FabBoard est un projet open-source développé par Res Fabrica. Nous accueillons les contributions de la communauté pour améliorer l'outil.

## 📬 Contact

Pour plus d'informations ou pour une démonstration personnalisée :

- Email : contact@resfabrica.fr
- Site web : https://resfabrica.fr

#FabLab #Maintenance #OpenSource #Innovation #MakerSpace #TechForGood

