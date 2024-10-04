## 📊 Monitoring avec Prometheus et Grafana

BrefBoard intègre Prometheus pour la collecte de métriques et Grafana pour la visualisation, offrant une surveillance en temps réel des performances de l'application.

### Installation de Prometheus

1. Téléchargez et installez Prometheus :
   ```
   wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
   tar -xvf prometheus-2.45.0.linux-amd64.tar.gz
   cd prometheus-2.45.0.linux-amd64
   sudo mv prometheus promtool /usr/local/bin/
   sudo mkdir /etc/prometheus /var/lib/prometheus
   sudo mv consoles/ console_libraries/ /etc/prometheus/
   sudo mv prometheus.yml /etc/prometheus/prometheus.yml
   ```

2. Configurez Prometheus en éditant `/etc/prometheus/prometheus.yml` :
   ```yaml
   global:
     scrape_interval: 15s

   scrape_configs:
     - job_name: 'brefboard'
       static_configs:
         - targets: ['localhost:8000']
   ```

3. Créez et démarrez le service Prometheus :
   ```
   sudo nano /etc/systemd/system/prometheus.service
   ```
   Ajoutez le contenu suivant :
   ```ini
   [Unit]
   Description=Prometheus Monitoring
   Wants=network-online.target
   After=network-online.target

   [Service]
   User=prometheus
   ExecStart=/usr/local/bin/prometheus --config.file=/etc/prometheus/prometheus.yml --storage.tsdb.path=/var/lib/prometheus/
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```
   Puis démarrez le service :
   ```
   sudo systemctl daemon-reload
   sudo systemctl start prometheus
   sudo systemctl enable prometheus
   ```

### Installation de Grafana

1. Installez Grafana :
   ```
   sudo apt-get install -y software-properties-common
   sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
   wget -q -O - https://packages.grafana.com/gpg.key | sudo apt-key add -
   sudo apt-get update
   sudo apt-get install grafana
   ```

2. Démarrez le service Grafana :
   ```
   sudo systemctl start grafana-server
   sudo systemctl enable grafana-server
   ```

### Configuration des métriques dans BrefBoard

BrefBoard utilise déjà `django-prometheus` pour exposer des métriques. Les principales métriques sont définies dans le fichier `metrics.py` :


De plus, BrefBoard utilise des middlewares personnalisés pour collecter des métriques supplémentaires. Ces middlewares sont définis dans le fichier `middleware.py` :

Les middlewares `ExceptionMiddleware` et `RequestMiddleware` sont responsables de :

1. Compter le nombre de requêtes par vue
2. Mesurer la latence des vues
3. Compter les erreurs HTTP
4. Compter les exceptions non gérées

Pour activer ces middlewares, assurez-vous qu'ils sont inclus dans la liste `MIDDLEWARE` de votre fichier `settings.py` :



Ces middlewares permettent une collecte automatique de métriques importantes pour surveiller la santé et les performances de l'application BrefBoard.


### Utilisation des décorateurs pour le monitoring

BrefBoard utilise des décorateurs personnalisés pour faciliter la collecte de métriques. Ces décorateurs sont définis dans le fichier `metrics.py` et sont utilisés dans les vues pour surveiller automatiquement certains aspects de l'application.

Voici les principaux décorateurs utilisés :

1. `@monitor_view` : Mesure le temps d'exécution d'une vue et incrémente le compteur de requêtes.
2. `@count_requests` : Incrémente le compteur de requêtes pour une vue spécifique.
3. `@measure_duration` : Mesure la durée d'exécution d'une fonction et l'enregistre dans un histogramme spécifié.
4. `@monitor_whisper_processing` : Surveille le temps de traitement de Whisper et enregistre les erreurs éventuelles.

Vous pouvez voir les exmeples d'utilisation dans le fichier `views.py` 



### Visualisation avec Grafana

1. Accédez à Grafana via `http://localhost:3000` (utilisateur/mot de passe par défaut : admin/admin).
2. Ajoutez Prometheus comme source de données.
3. Créez un nouveau tableau de bord avec des panneaux pour les métriques importantes, comme :
   - Temps de réponse des vues Django
   - Nombre d'enregistrements audio
   - Durée des tâches de transcription
   - Qualité des transcriptions
   - Temps de génération des résumés

### Bonnes pratiques

- Assurez-vous que l'endpoint `/metrics` n'est accessible qu'en interne ou protégé par une authentification.
- Évitez d'exposer des informations sensibles dans les métriques.
- Mettez régulièrement à jour Prometheus, Grafana et `django-prometheus`.

Pour plus de détails sur l'utilisation et la configuration avancée, consultez la documentation officielle de [Prometheus](https://prometheus.io/docs/introduction/overview/) et [Grafana](https://grafana.com/docs/).