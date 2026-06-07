from django.core.cache import cache
from django.utils import timezone

from .models import User

LAST_SEEN_THROTTLE_SECONDS = 60


def _throttle_key(user_id):
    return f"last_seen_touched:{user_id}"


class LastSeenMiddleware:
    """Update User.last_seen_at on authenticated requests, throttled to once per minute."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        user = getattr(request, "user", None)
        if user and user.is_authenticated:
            key = _throttle_key(user.id)
            if cache.get(key) is None:
                cache.set(key, 1, timeout=LAST_SEEN_THROTTLE_SECONDS)
                User.objects.filter(pk=user.id).update(last_seen_at=timezone.now())
        return response
