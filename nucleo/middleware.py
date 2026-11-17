from django.conf import settings
from django.http import HttpResponse


class SimpleCorsMiddleware:
    """Attach explicit CORS headers when CORS_ALLOWED_ORIGINS is configured."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
        origin = request.META.get('HTTP_ORIGIN')
        origin_allowed = bool(origin and origin in allowed)

        if request.method == 'OPTIONS' and origin_allowed:
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        if origin_allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type, X-CSRFToken'
            response['Vary'] = 'Origin'
        return response
