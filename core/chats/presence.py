from django.core.cache import cache

ONLINE_TTL_SECONDS = 60


def _key(user_id):
    return f"presence:online:{user_id}"


def mark_online(user_id):
    cache.set(_key(user_id), 1, timeout=ONLINE_TTL_SECONDS)


def mark_offline(user_id):
    cache.delete(_key(user_id))


def is_online(user_id):
    return cache.get(_key(user_id)) is not None
