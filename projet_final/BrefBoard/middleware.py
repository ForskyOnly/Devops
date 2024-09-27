from .metrics import EXCEPTION_COUNTER

class ExceptionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_exception(self, request, exception):
        EXCEPTION_COUNTER.labels(type=type(exception).__name__).inc()