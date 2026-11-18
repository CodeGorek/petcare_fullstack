import time
from collections import defaultdict, deque
from threading import Lock
from django.conf import settings
from django.http import HttpResponse, JsonResponse


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


class RateLimitMiddleware:
    """Protect backend endpoints from request bursts when RATE_LIMIT_PER_MIN > 0."""

    _hits = defaultdict(deque)
    _lock = Lock()

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        limit = int(getattr(settings, 'RATE_LIMIT_PER_MIN', 0) or 0)
        if limit > 0:
            forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
            ip = (forwarded.split(',')[0].strip() if forwarded else request.META.get('REMOTE_ADDR')) or 'unknown'
            now = time.monotonic()
            cutoff = now - 60.0
            with self._lock:
                bucket = self._hits[ip]
                while bucket and bucket[0] < cutoff:
                    bucket.popleft()
                if len(bucket) >= limit:
                    return JsonResponse(
                        {'detail': 'Demasiadas solicitudes (Rate Limit activo). Reintenta en unos segundos.'},
                        status=429,
                    )
                bucket.append(now)
        return self.get_response(request)
