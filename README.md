# 🎙️ BrefBoard

#### projet complet dans le dossier projet_final

## 📚 Table des matières

1. [Description](#-description)
2. [Fonctionnalités principales](#-fonctionnalités-principales)
3. [Technologies utilisées](#️-technologies-utilisées)
4. [Structure du projet](#-structure-du-projet)
5. [Installation et utilisation](#-installation-et-utilisation)
6. [Utilisation avec Docker](#-utilisation-avec-docker)
7. [Déploiement sur Azure](#️-déploiement-sur-azure)
8. [Monitoring avec Prometheus et Grafana](#-monitoring-avec-prometheus-et-grafana)
9. [Licence](#-licence)



## 📝 Description

BrefBoard est une application web  conçue pour simplifier la prise de notes et la transcription de réunions. Elle utilise des technologies de pointe pour l'enregistrement audio, la transcription en temps réel et la génération de résumés intelligents.


## 🌟 Fonctionnalités principales

- 🎤 Enregistrement audio en temps réel
- 📝 Transcription automatique du discours
- 🤖 Génération de résumés avec l'IA
- 📊 Gestion et visualisation des transcriptions et résumés
- 🌓 Mode sombre/clair pour une meilleure expérience utilisateur
- 📥 Téléchargement des transcriptions et résumés en formats TXT et PDF

## 🛠️ Technologies utilisées

- Django (Backend)
- HTML, CSS, JavaScript (Frontend)
- MySQL (Base de données)
- Whisper (Transcription audio)
- Mistral AI (Génération de résumés)
- Docker (Conteneurisation)
- Prometheus (Monitoring)
- Grafana (Visualisation)
- Azure (Déploiement cloud)


## 📁 Structure du projet


```pprojet_final/
├── BrefBoard/ # Application principale
│ ├── static/ # Fichiers statiques (CSS, JS)
│ ├── templates/ # Templates HTML
│ ├── migrations/ # Migrations de la base de données
│ ├── models.py # Modèles de données
│ ├── views.py # Logique de vue
│ ├── forms.py # Formulaires
│ └── tests.py # Tests unitaires
│ └── metrics.py # Métriques Voir MONITORING.md
│ └── middleware.py # Middleware Voir MONITORING.md
│
├── projet_final/ # Configuration du projet
│ ├── settings/ # Paramètres (dev, prod)
│ └── urls.py # Configuration des URLs
│
├── manage.py # Script de gestion Django
├── Dockerfile # Configuration Docker
├── requirements.txt # Dépendances Python
├── entrypoint.sh # Script d'entrée pour Docker
├── Az_create_mysql.sh # Script de création de la base de données Azure
├── Az_delete_az.sh # Script de suppression des ressources Azure
└── Az_migrate_create_tabs.sh # Script de migration et création de tables
```


## 🚀 Installation et utilisation

1. Clonez le dépôt :
   ```
   git clone https://github.com/votre-username/BrefBoard.git
   cd BrefBoard
   ```

2. Créez un environnement virtuel et installez les dépendances :
   ```
   python -m venv venv
   source venv/bin/activate  # Sur Windows : venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Configurez les variables d'environnement dans un fichier `.env` à la racine du projet :
   ```
   SECRET_KEY=votre_cle_secrete
   MISTRAL_API_KEY=votre_cle_api_mistral
   DATABASE=nom_de_votre_base_de_donnees
   DATABASE_HOST=hote_de_votre_base_de_donnees
   DATABASE_PORT=port_de_votre_base_de_donnees
   PASSWORD=mot_de_passe_de_votre_base_de_donnees
   NOMUSER=nom_utilisateur_base_de_donnees
   ```

4. Appliquez les migrations :
   ```
   python manage.py migrate
   ```

5. Lancez le serveur de développement :
   ```
   DJANGO_SETTINGS_MODULE=projet_final.settings.development python manage.py runserver 
   ```

6. Pour les conditions de production, utilisez :
   ```
   DJANGO_SETTINGS_MODULE=projet_final.settings.production python manage.py runserver 
   ```

7. Accédez à l'application dans votre navigateur à `http://localhost:8000`

## 🐳 Utilisation avec Docker

1. Construisez l'image Docker :
   ```
      docker build -t usernameDocker/NomDeVotreApp:latest .
   ```

2. Lancez le conteneur :
   ```
   docker run -p 8000:8000 usernameDocker/NomDeVotreApp:latest
   ```

3. Accédez à l'application à `http://localhost:8000`

## ☁️ Déploiement sur Azure

1. Assurez-vous d'avoir installé Azure CLI et d'être connecté à votre compte Azure.

2. Exécutez le script de création de ressources Azure :
   ```
   ./Az_create_mysql.sh
   ```

3. Crée et migrer les tables dans la base de données Azure :
   ```
   ./Az_migrate_create_tabs.sh
   ```

4. Déployez l'application sur Azure :

   nb: Le cicd mis en place permet de faire les test et push sur docker hub vous pouvez configurer les secrets si vous souhaitez inclure le deployement dans le cicd,
   voici un template pour le deploiement :
   ```
   az login

      az container create \
      --resource-group <VOTRE_GROUPE_DE_RESSOURCES> \
      --name <NOM_DU_CONTENEUR> \
      --image <VOTRE_IMAGE_DOCKER> \
      --cpu 1 \ # nombre de coeurs
      --memory 2 \ # ram allouée 
      --ports 80 8000 \ 
      --dns-name-label <VOTRE_LABEL_DNS> \ 
      --environment-variables \
         DJANGO_SETTINGS_MODULE=projet_final.settings.production \
         RESOURCE_GROUP=<VOTRE_GROUPE_DE_RESSOURCES> \
         LOCATION=<VOTRE_REGION> \
         SERVER_NAME=<NOM_SERVEUR_BDD> \
         DATABASE_PORT=<PORT_BDD> \
         DATABASE=<NOM_BDD> \
         DATABASE_HOST=<HOTE_BDD> \
         SUBSCRIPTION_ID=<VOTRE_ID_SOUSCRIPTION> \
         API_KEY_NAME=<NOM_CLE_API> \
         WEBSITE_HOSTNAME=<VOTRE_NOM_HOTE>.azurecontainer.io \
         STATIC_URL=/static/ \
         STATIC_ROOT=/app/BrefBoard/staticfiles \
         WEB_CONCURRENCY=2 \
         GUNICORN_CMD_ARGS="--workers=2 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm" \
      --secure-environment-variables \
         SECRET_KEY='<VOTRE_CLE_SECRETE>' \
         MISTRAL_API_KEY='<VOTRE_CLE_API_MISTRAL>' \
         NOMUSER=<UTILISATEUR_BDD> \
         PASSWORD='<MOT_DE_PASSE_BDD>' \
         API_KEY=<VOTRE_CLE_API>
   ```



## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.
