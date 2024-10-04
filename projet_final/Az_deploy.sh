az login

az container create \
  --resource-group RG_RUBIC \
  --name bref-board-container \
  --image forskyonly/brefboard:latest \
  --cpu 1 \
  --memory 2 \
  --ports 80 8000 \
  --dns-name-label bref-board-dns \
  --environment-variables \
    DJANGO_SETTINGS_MODULE=projet_final.settings.production \
    RESOURCE_GROUP=RG_RUBIC \
    LOCATION=francecentral \
    SERVER_NAME=rubic-server \
    DATABASE_PORT=3306 \
    DATABASE=SpeechToSummerize \
    DATABASE_HOST=rubic-server.mysql.database.azure.com \
    SUBSCRIPTION_ID=111aaa69-41b9-4dfd-b6af-2ada039dd1ae \
    API_KEY_NAME=access_token \
    WEBSITE_HOSTNAME=bref-board-dns.francecentral.azurecontainer.io \
    STATIC_URL=/static/ \
    STATIC_ROOT=/app/BrefBoard/staticfiles \
    WEB_CONCURRENCY=2 \
    GUNICORN_CMD_ARGS="--workers=2 --threads=4 --worker-class=gthread --worker-tmp-dir /dev/shm" \
  --secure-environment-variables \
    SECRET_KEY='Su_persec_retkeyd_eouf123**02' \
    MISTRAL_API_KEY='FJUleWCFqW3kUma8OQKGOzT9M3UOQUuW' \
    NOMUSER=rubic \
    PASSWORD='Jsnl2d12e' \
    API_KEY=azerty