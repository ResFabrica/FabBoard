# FabBoard

FabBoard est une application web Django pour la gestion de FabLabs, permettant de suivre les projets, les tâches et la maintenance des machines.

## Fonctionnalités

- Gestion des utilisateurs et des FabLabs
- Gestion des projets avec système de vues personnalisables
- Suivi des tâches avec assignation d'utilisateurs et dates limites
- Système de tags pour l'organisation
- Champs personnalisés pour les tâches
- Gestion des fichiers attachés
- Interface responsive et moderne

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

FabBoard est une application web open-source conçue pour simplifier la gestion de la maintenance des machines dans les FabLabs. Développée avec Django, elle offre une interface intuitive permettant aux équipes de suivre et planifier les opérations de maintenance de leur parc machines.

## ✨ Fonctionnalités Principales

- **Gestion Multi-FabLabs**
  - Chaque FabLab gère son propre parc de machines
  - Interface dédiée par FabLab
  - Collaboration entre membres d'un même FabLab
- **Gestion des Machines**
  - Ajout de machines avec photos et caractéristiques
  - Types de machines prédéfinis (Imprimantes 3D, Découpeuses Laser, etc.)
  - Possibilité d'ajouter des types personnalisés
- **Suivi des Maintenances**
  - Planification de maintenances récurrentes
  - Maintenances ponctuelles
  - Historique complet des interventions
  - Notifications pour les maintenances à venir (7 jours)
- **Types de Maintenance Prédéfinis**
  - Imprimantes 3D : Nettoyage print core, calibration plateau, etc.
  - Découpeuses Laser : Nettoyage optique, changement filtres, etc.
  - Types personnalisables par machine
- **Accès Public**
  - Lien public par machine pour les interventions externes
  - Interface simplifiée pour les intervenants occasionnels

## 🚀 Démo

Vous souhaitez tester FabBoard ?

1. Rendez-vous sur [maintenance.resfabrica.fr](https://maintenance.resfabrica.fr)
2. Créez un compte avec votre email
3. Ajoutez votre premier FabLab
4. Commencez à gérer vos machines !

## 💡 Cas d'Usage

- **FabLabs** : Gestion complète du parc machines
- **Makerspaces** : Suivi des maintenances préventives
- **Ateliers Partagés** : Coordination des interventions
- **Écoles & Universités** : Maintenance des équipements pédagogiques

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

