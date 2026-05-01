# Python modules
from urllib.parse import parse_qs

# Third-party modules
from channels.db import database_sync_to_async


@database_sync_to_async
def get_user_from_token(token: str) -> None:
    """
    Gets a user from the given JWT token. If the token is invalid or expired, returns an AnonymousUser.
    """
    from django.contrib.auth.models import AnonymousUser
    from rest_framework_simplejwt.tokens import AccessToken
    from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
    from apps.users.models import CustomUser

    try:
        access_token = AccessToken(token)
        user_id = access_token.get("user_id")
        if user_id is None:
            return AnonymousUser()
        return CustomUser.objects.filter(id=user_id).first()
    except (InvalidToken, TokenError):
        return AnonymousUser()


class AuthWebsocketMiddleware:
    """
    Auth middleware for WebSocket connections. It can be used to authenticate users based on tokens or session cookies.
    """

    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send) -> None:
        from django.contrib.auth.models import AnonymousUser

        query_string = scope.get("query_string", b"").decode()
        parsed_query_string = parse_qs(query_string)
        token = parsed_query_string.get("token", [None])[0]
        if token:
            scope["user"] = await get_user_from_token(token)
        else:
            scope["user"] = AnonymousUser()

        return await self.inner(scope, receive, send)
