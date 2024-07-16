#!/bin/bash

# Charger les variables d'environnement depuis le fichier .env
set -o allexport
source .env
set +o allexport


# Supprimer le groupe de ressources
az group delete \
  --name $RESOURCE_GROUP \
  --yes
