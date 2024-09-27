from prometheus_client import Counter, Histogram, Gauge
import time
from functools import wraps

# Compteurs pour les erreurs
ERROR_COUNTER = Counter('django_error_total', 'Total number of Django errors', ['type'])

# Histogramme pour la latence des vues
VIEW_LATENCY = Histogram('django_view_latency_seconds', 'Latency of views', ['view_name'])

# Compteur pour les exceptions non gérées
EXCEPTION_COUNTER = Counter('django_exceptions_total', 'Total number of unhandled exceptions', ['type'])

# Compteur pour les requêtes
REQUEST_COUNT = Counter('django_request_count', 'Number of requests per view', ['view_name'])

# Compteur pour les enregistrements audio
AUDIO_RECORDINGS = Counter('django_audio_recordings_total', 'Number of audio recordings')

# Histogramme pour la durée des tâches de transcription
TRANSCRIPTION_DURATION = Histogram('django_transcription_duration_seconds', 'Duration of transcription tasks')

# Nouvelles métriques pour Whisper et l'enregistrement
WHISPER_PROCESSING_TIME = Histogram('whisper_processing_time_seconds', 'Time taken by Whisper to process audio')
WHISPER_ERRORS = Counter('whisper_errors_total', 'Number of errors during Whisper processing', ['error_type'])
AUDIO_DURATION = Histogram('audio_duration_seconds', 'Duration of recorded audio')
RECORDING_ERRORS = Counter('recording_errors_total', 'Number of errors during audio recording', ['error_type'])
RECORDING_QUALITY = Gauge('recording_quality', 'Quality metric of the recorded audio')

def count_requests(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        REQUEST_COUNT.labels(view_name=view_func.__name__).inc()
        return view_func(request, *args, **kwargs)
    return wrapper

def monitor_view(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        start_time = time.time()
        try:
            return view_func(request, *args, **kwargs)
        finally:
            latency = time.time() - start_time
            VIEW_LATENCY.labels(view_name=view_func.__name__).observe(latency)
    return wrapper

def monitor_whisper_processing(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            WHISPER_PROCESSING_TIME.observe(time.time() - start_time)
            return result
        except Exception as e:
            WHISPER_ERRORS.labels(error_type=type(e).__name__).inc()
            raise
    return wrapper

def record_audio_duration(duration):
    AUDIO_DURATION.observe(duration)

def record_audio_quality(quality_score):
    RECORDING_QUALITY.set(quality_score)

def increment_recording_error(error_type):
    RECORDING_ERRORS.labels(error_type=error_type).inc()

# Fonction utilitaire pour mesurer la durée d'exécution
def measure_duration(metric):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with metric.time():
                return func(*args, **kwargs)
        return wrapper
    return decorator