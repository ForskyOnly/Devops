#!/bin/bash

# Charger les variables d'environnement
source .env 

# Connexion à Azure
az login

# Définir la souscription
az account set --subscription $SUBSCRIPTION_ID

# Créer un plan App Service (si non existant)
az appservice plan create --name bref-board-plan --resource-group $RESOURCE_GROUP --sku B1 --is-linux

# Créer une Web App pour conteneurs
az webapp create --resource-group $RESOURCE_GROUP --plan bref-board-plan --name bref-board --deployment-container-image-name forskyonly/brefboard:latest

# Configurer les variables d'environnement pour l'application
az webapp config appsettings set --resource-group $RESOURCE_GROUP --name bref-board --settings \
    SECRET_KEY="$SECRET_KEY" \
    DJANGO_SETTINGS_MODULE="$DJANGO_SETTINGS_MODULE" \
    MISTRAL_API_KEY="$MISTRAL_API_KEY" \
    RESOURCE_GROUP="$RESOURCE_GROUP" \
    LOCATION="$LOCATION" \
    SERVER_NAME="$SERVER_NAME" \
    NOMUSER="$NOMUSER" \
    PASSWORD="$PASSWORD" \
    DATABASE_PORT="$DATABASE_PORT" \
    DATABASE="$DATABASE" \
    DATABASE_HOST="$DATABASE_HOST" \
    SUBSCRIPTION_ID="$SUBSCRIPTION_ID" \
    API_KEY_NAME="$API_KEY_NAME" \
    API_KEY="$API_KEY"

# Configurer les paramètres de connexion à la base de données
az webapp config connection-string set --resource-group $RESOURCE_GROUP --name bref-board --connection-string-type MySQL \
    --settings DefaultConnection="Server=$DATABASE_HOST; Database=$DATABASE; Uid=$NOMUSER; Pwd=$PASSWORD;"

# Configurer le pare-feu de la base de données pour autoriser l'App Service
OUTBOUND_IP_ADDRESSES=$(az webapp show --resource-group $RESOURCE_GROUP --name bref-board --query outboundIpAddresses --output tsv)
IFS=',' read -ra IP_ARRAY <<< "$OUTBOUND_IP_ADDRESSES"
for IP in "${IP_ARRAY[@]}"; do
    az mysql flexible-server firewall-rule create \
        --resource-group $RESOURCE_GROUP \
        --name $SERVER_NAME \
        --rule-name "AllowAppService_$IP" \
        --start-ip-address $IP \
        --end-ip-address $IP
done

# Autoriser les services Azure à accéder au serveur MySQL flexible
az mysql flexible-server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --name $SERVER_NAME \
    --rule-name AllowAzureServices \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255

# Activer HTTPS et forcer HTTPS
az webapp update --resource-group $RESOURCE_GROUP --name bref-board --https-only true

# Configurer les paramètres TLS/SSL
az webapp config set --resource-group $RESOURCE_GROUP --name bref-board --min-tls-version 1.2

# Redémarrer l'application pour appliquer les changements
az webapp restart --name bref-board --resource-group $RESOURCE_GROUP

echo "Déploiement terminé. Votre application devrait être accessible en HTTPS à l'adresse https://bref-board.azurewebsites.net"