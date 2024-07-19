#!/bin/bash

# Charger les variables d'environnement du fichier .env
set -o allexport
source .env
set +o allexport

# Se connecter à Azure
az login

# Définir l'ID de l'abonnement
az account set --subscription $SUBSCRIPTION_ID

# Créer un nouveau groupe de ressources s'il n'existe pas
az group create --name $RESOURCE_GROUP --location $LOCATION

# Créer un nouveau serveur MySQL flexible
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

# Obtenir l'adresse IPv4 publique actuelle
MY_IP=$(curl -4 ifconfig.me)

# Configurer le pare-feu pour permettre l'accès à partir de l'adresse IPv4 actuelle
az mysql flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --rule-name AllowMyIPv4 \
    --start-ip-address $MY_IP \
    --end-ip-address $MY_IP

# Créer une nouvelle base de données MySQL
az mysql flexible-server db create --resource-group $RESOURCE_GROUP --server-name $SERVER_NAME --database-name $DATABASE

# Afficher les détails du serveur MySQL
az mysql flexible-server show --resource-group $RESOURCE_GROUP --name $SERVER_NAME

# Installer le client MySQL s'il n'est pas déjà installé
if ! command -v mysql &> /dev/null
then
    echo "Client MySQL introuvable. Installation de MySQL client..."
    sudo apt-get update
    sudo apt-get install mysql-client -y
fi

# Indiquer l'achèvement de la première partie
echo "Configuration Azure et MySQL terminée. Procédez avec le script de migration Django et de création des tables."
