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

# Create a new MySQL flexible server with a unique name
UNIQUE_SERVER_NAME="rubics-mysql-$(date +%s)"
az mysql flexible-server create \
    --name $UNIQUE_SERVER_NAME \
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
    --name $UNIQUE_SERVER_NAME \
    --rule-name AllowMyIPv4 \
    --start-ip-address $MY_IP \
    --end-ip-address $MY_IP

# Create a new MySQL database
az mysql flexible-server db create --resource-group $RESOURCE_GROUP --server-name $UNIQUE_SERVER_NAME --database-name $DATABASE

# Show the MySQL server details
az mysql flexible-server show --resource-group $RESOURCE_GROUP --name $UNIQUE_SERVER_NAME

# Install MySQL client if not already installed
if ! command -v mysql &> /dev/null
then
    echo "MySQL client could not be found. Installing..."
    sudo apt-get update
    sudo apt-get install mysql-client -y
fi

# Download the SSL certificate
wget --no-check-certificate -O /home/utilisateur/Documents/dev/devia/Devops/projet_final/DigiCertGlobalRootCA.crt.pem https://www.digicert.com/CACerts/DigiCertGlobalRootCA.crt.pem

# Connect to the MySQL server as 'rubic' and create the tables
mysql -u rubic@rubics-mysql-1721293694 -p$PASSWORD -h rubics-mysql-1721293694.mysql.database.azure.com --ssl-ca=/home/utilisateur/Documents/dev/devia/Devops/projet_final/DigiCertGlobalRootCA.crt.pem --ssl-mode=VERIFY_CA $DATABASE << EOF
USE $DATABASE;

CREATE TABLE Audio (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    file_url VARCHAR(255) NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES auth_user(id)
);

CREATE TABLE Transcription (
    id INT AUTO_INCREMENT PRIMARY KEY,
    audio_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (audio_id) REFERENCES Audio(id)
);

CREATE TABLE Summary (
    id INT AUTO_INCREMENT PRIMARY KEY,
    transcription_id INT NOT NULL,
    text LONGTEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (transcription_id) REFERENCES Transcription(id)
);

CREATE USER 'admin'@'%' IDENTIFIED BY 'password';
GRANT SELECT, INSERT, UPDATE ON $DATABASE.* TO 'admin'@'%';
FLUSH PRIVILEGES;
EOF
