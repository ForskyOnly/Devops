from .metrics import EXCEPTION_COUNTER, ERROR_COUNTER, VIEW_LATENCY, REQUEST_COUNT
import time


class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Incrémenter le compteur de requêtes
        REQUEST_COUNT.labels(view_name=request.resolver_match.view_name).inc()
        
        response = self.get_response(request)
        
        # Mesurer la latence de la vue
        latency = time.time() - start_time
        VIEW_LATENCY.labels(view_name=request.resolver_match.view_name).observe(latency)
        
        # Compter les erreurs HTTP
        if 400 <= response.status_code < 600:
            ERROR_COUNTER.labels(type=f'HTTP_{response.status_code}').inc()
        
        return response

    def process_exception(self, request, exception):
        # Compter les exceptions non gérées
        EXCEPTION_COUNTER.labels(type=type(exception).__name__).inc()
        
        ERROR_COUNTER.labels(type='Unhandled_Exception').inc()