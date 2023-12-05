# Utiliser une image Python officielle comme image de base
FROM python:3.9

# Définir le répertoire de travail dans le conteneur
WORKDIR /app

# Copier les fichiers 'requirements.txt' dans le répertoire de travail
COPY requirements.txt /app/

# Installer les dépendances
RUN pip install --no-cache-dir -r requirements.txt

# Copier le reste du code de l'application dans le répertoire de travail
COPY . /app/

# Définir la variable d'environnement pour exécuter Django en mode production
ENV DJANGO_SETTINGS_MODULE=projet_final.settings

# Collecter les fichiers statiques
RUN python manage.py collectstatic --noinput

# Exposer le port sur lequel l'application va s'exécuter
EXPOSE 8000

# Commande pour démarrer l'application avec Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "projet_final.wsgi:application"]
