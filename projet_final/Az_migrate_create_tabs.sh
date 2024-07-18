#!/bin/bash

# Charger les variables d'environnement du fichier .env
set -o allexport
source .env
set +o allexport

# Effectuer les migrations Django
python manage.py migrate || { echo 'Django migration failed' ; exit 1; }

# Se connecter au serveur MySQL et créer les tables supplémentaires
mysql -h $DATABASE_HOST -u $USERNAME -p$PASSWORD --ssl-mode=DISABLED $DATABASE << EOF
USE $DATABASE;

CREATE TABLE IF NOT EXISTS Audio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Transcription (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audio_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcription_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF
echo "Migration et création des tables terminé."

# Se connecter au serveur MySQL et ajouter les clés étrangères
mysql -h $DATABASE_HOST -u $USERNAME -p$PASSWORD --ssl-mode=DISABLED $DATABASE << EOF
USE $DATABASE;

ALTER TABLE Audio
ADD FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE Transcription
ADD FOREIGN KEY (audio_id) REFERENCES Audio(id);

ALTER TABLE Summary
ADD FOREIGN KEY (transcription_id) REFERENCES Transcription(id);
EOF
echo "Ajout des clé primaire et clés étrangères terminé"
