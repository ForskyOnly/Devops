# 🎙️ BrefBoard

## 📝 Description

BrefBoard est une application web innovante conçue pour simplifier la prise de notes et la transcription de réunions. Elle utilise des technologies de pointe pour l'enregistrement audio, la transcription en temps réel et la génération de résumés intelligents.

## 🌟 Fonctionnalités principales

- 🎤 Enregistrement audio en temps réel
- 📝 Transcription automatique du discours
- 🤖 Génération de résumés avec l'IA
- 📊 Gestion et visualisation des transcriptions et résumés
- 🌓 Mode sombre/clair pour une meilleure expérience utilisateur

## 🛠️ Technologies utilisées

- Django (Backend)
- HTML, CSS, JavaScript (Frontend)
- MySQL (Base de données)
- Whisper (Transcription audio)
- Mistral AI (Génération de résumés)
- Docker (Conteneurisation)

## 📁 Structure du projet

projet_final/
│
├── BrefBoard/ # Application principale
│ ├── static/ # Fichiers statiques (CSS, JS)
│ ├── templates/ # Templates HTML
│ ├── models.py # Modèles de données
│ ├── views.py # Logique de vue
│ └── forms.py # Formulaires
│
├── projet_final/ # Configuration du projet
│ ├── settings/ # Paramètres (dev, prod)
│ └── urls.py # Configuration des URLs
│
├── manage.py # Script de gestion Django
├── Dockerfile # Configuration Docker
├── docker-compose.yml # Configuration Docker Compose
└── requirements.txt # Dépendances Python


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
   ```

4. Appliquez les migrations :
   ```
   python manage.py migrate
   ```

5. Lancez le serveur de développement :
   ```
   python manage.py runserver
   ```

6. Accédez à l'application dans votre navigateur à `http://localhost:8000`

## 🐳 Utilisation avec Docker

1. Construisez l'image Docker :
   ```
   docker-compose build
   ```

2. Lancez les conteneurs :
   ```
   docker-compose up
   ```

3. Accédez à l'application à `http://localhost:8000`

## 👥 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## 📄 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.


---

🌟 Merci d'utiliser BrefBoard ! Nous espérons que cette application vous aidera à optimiser vos réunions et à améliorer votre productivité.