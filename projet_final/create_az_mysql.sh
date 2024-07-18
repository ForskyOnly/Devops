#!/bin/bash

# Load environment variables from .env file
set -o allexport
source .env
set +o allexport

# Login to Azure
az login

# Set the subscription ID
az account set --subscription $SUBSCRIPTION_ID

# Create a new resource group if it doesn't exist
az group create --name $RESOURCE_GROUP --location $LOCATION

# Define the server name manually
SERVER_NAME="rubic-server"  # Remplacez par votre nom de serveur
DATABASE="SpeechToSummerize"  # Remplacez par votre nom de base de données

# Create a new MySQL flexible server
az mysql flexible-server create \
    --name $SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $USERNAME \
    --admin-password $PASSWORD \
    --sku-name Standard_B1ms \
    --storage-size 32 \
    --version 8.0.21 \
    --public-access 0.0.0.0-255.255.255.255

# Get the current public IPv4 address
MY_IP=$(curl -4 ifconfig.me)

# Configure firewall to allow access from the current IPv4 address
az mysql flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --rule-name AllowMyIPv4 \
    --start-ip-address $MY_IP \
    --end-ip-address $MY_IP

# Create a new MySQL database
az mysql flexible-server db create --resource-group $RESOURCE_GROUP --server-name $SERVER_NAME --database-name $DATABASE

# Show the MySQL server details
az mysql flexible-server show --resource-group $RESOURCE_GROUP --name $SERVER_NAME

# Install MySQL client if not already installed
if ! command -v mysql &> /dev/null
then
    echo "MySQL client could not be found. Installing..."
    sudo apt-get update
    sudo apt-get install mysql-client -y
fi

# Download the SSL certificate
wget --no-check-certificate -O /home/utilisateur/Documents/dev/devia/Devops/projet_final/DigiCertGlobalRootCA.crt.pem https://www.digicert.com/CACerts/DigiCertGlobalRootCA.crt.pem

# Perform Django migrations
python manage.py migrate

# Connect to the MySQL server and create the additional tables
mysql -u rubic@$SERVER_NAME -p$PASSWORD -h $SERVER_NAME.mysql.database.azure.com --ssl-ca=/home/utilisateur/Documents/dev/devia/Devops/projet_final/DigiCertGlobalRootCA.crt.pem --ssl-mode=VERIFY_CA $DATABASE << EOF
USE $DATABASE;

CREATE TABLE Audio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Transcription (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audio_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE Summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcription_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOF

# Connect to the MySQL server and add the foreign keys
mysql -u rubic@$SERVER_NAME -p$PASSWORD -h $SERVER_NAME.mysql.database.azure.com --ssl-ca=/home/utilisateur/Documents/dev/devia/Devops/projet_final/DigiCertGlobalRootCA.crt.pem --ssl-mode=VERIFY_CA $DATABASE << EOF
USE $DATABASE;

ALTER TABLE Audio
ADD FOREIGN KEY (user_id) REFERENCES auth_user(id);

ALTER TABLE Transcription
ADD FOREIGN KEY (audio_id) REFERENCES Audio(id);

ALTER TABLE Summary
ADD FOREIGN KEY (transcription_id) REFERENCES Transcription(id);
EOF
