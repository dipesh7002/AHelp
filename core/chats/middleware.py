from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.authentication import JWTAuthentication


@database_sync_to_async
def get_user_for_token(token):
    if not token:
        return AnonymousUser()
    authenticator = JWTAuthentication()
    try:
        validated_token = authenticator.get_validated_token(token)
        return authenticator.get_user(validated_token)
    except Exception:
        return AnonymousUser()


class JWTAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query = parse_qs(scope.get("query_string", b"").decode())
        token = query.get("token", [None])[0]

        if not token:
            for name, value in scope.get("headers", []):
                if name == b"sec-websocket-protocol":
                    protocols = [part.strip() for part in value.decode().split(",")]
                    token = next((part.removeprefix("token.") for part in protocols if part.startswith("token.")), None)
                    break

        scope["user"] = await get_user_for_token(token)
        return await self.inner(scope, receive, send)
