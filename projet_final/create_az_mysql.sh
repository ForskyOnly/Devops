#!/bin/bash

# Load environment variables from .env file
set -o allexport
source .env
set +o allexport

# Login
az login 

# Set the subscription ID
az account set --subscription $SUBSCRIPTION_ID

# Create a new resource group
az group create --name $RESOURCE_GROUP --location $LOCATION

# Create a new MySQL server
az mysql server create \
    --name $SERVER_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --admin-user $USERNAME \
    --admin-password $PASSWORD \
    --sku-name B_Gen5_1 \
    --version 8.0 \
    --ssl-enforcement Disabled \
    --public all

# Configure firewall to allow access from all IPs
az mysql server firewall-rule create \
    --resource-group $RESOURCE_GROUP \
    --server $SERVER_NAME \
    --name AllowAllIPs \
    --start-ip-address 0.0.0.0 \
    --end-ip-address 255.255.255.255

# Create a new MySQL database
az mysql db create --resource-group $RESOURCE_GROUP --server-name $SERVER_NAME --name $DATABASE 

# Show the MySQL server details
az mysql server show --resource-group $RESOURCE_GROUP --name $SERVER_NAME

# Connect to the MySQL server and create the tables
MYSQL_HOST=$SERVER_NAME.mysql.database.azure.com
MYSQL_PORT=3306

mysql -u $USERNAME@$SERVER_NAME -p$PASSWORD -h $MYSQL_HOST -P $MYSQL_PORT $DATABASE << EOF
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
EOF
