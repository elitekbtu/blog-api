# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from rest_framework import serializers
from rest_framework.response import Response as DRFResponse
from rest_framework.request import Request as DRFRequest
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
    inline_serializer,
)

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


# Project modules
from apps.users.auth.serializers import RegistrationSerializer, LoginSerializer
from apps.abstract.ratelimit import ratelimit, get_client_ip

logger = logging.getLogger(__name__)



ValidationErrorResponse = inline_serializer(
    name="ValidationErrorResponse",
    fields={
        "detail": serializers.CharField(required=False),
        "non_field_errors": serializers.ListField(
            child=serializers.CharField(), required=False
        ),
    },
)

RateLimitErrorResponse = inline_serializer(
    name="RateLimitErrorResponse",
    fields={
        "detail": serializers.CharField(),
    },
)


@extend_schema_view(
    login=extend_schema(
        tags=["Auth"],
        summary="Authenticate user and issue JWT tokens",
        description=(
            "Authenticates a user by email/password and returns JWT access/refresh tokens. "
            "Authentication is not required. Side effects: writes login audit logs and applies "
            "IP-based rate limiting (10 requests per minute). Language behavior: validation/error "
            "messages may be localized by active request language. Timezone behavior: not applicable.\n\n"
            "Request example:\n"
            "POST /api/auth/token/\n"
            "{\n"
            "  \"email\": \"alice@example.com\",\n"
            "  \"password\": \"StrongPass123\"\n"
            "}\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"access\": \"<jwt-access-token>\",\n"
            "  \"refresh\": \"<jwt-refresh-token>\"\n"
            "}"
        ),
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                response=LoginSerializer,
                description="Authenticated successfully and returned access/refresh tokens.",
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponse,
                description="Validation failed or invalid credentials.",
            ),
            429: OpenApiResponse(
                response=RateLimitErrorResponse,
                description="Too many login attempts from the same client IP.",
            ),
        },
        examples=[
            OpenApiExample(
                "Login Request",
                value={
                    "email": "alice@example.com",
                    "password": "StrongPass123",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Login Success",
                value={
                    "access": "<jwt-access-token>",
                    "refresh": "<jwt-refresh-token>",
                },
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Login Validation Error",
                value={"non_field_errors": ["Invalid email or password"]},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Login Rate Limit Error",
                value={"detail": "Too many requests. Try again later."},
                response_only=True,
                status_codes=["429"],
            ),
        ],
    ),
    register=extend_schema(
        tags=["Auth"],
        summary="Register a new user account",
        description=(
            "Creates a new user and returns profile fields with issued JWT tokens. "
            "Authentication is not required. Side effects: sends a welcome email after successful "
            "account creation, writes registration logs, and applies IP-based rate limiting "
            "(5 requests per minute). Language behavior: validation/error messages may be localized "
            "by active request language. Timezone behavior: user timezone defaults to UTC unless "
            "changed later via preferences.\n\n"
            "Request example:\n"
            "POST /api/auth/register/\n"
            "{\n"
            "  \"email\": \"alice@example.com\",\n"
            "  \"first_name\": \"Alice\",\n"
            "  \"last_name\": \"Smith\",\n"
            "  \"preferred_language\": \"en\",\n"
            "  \"password\": \"StrongPass123\",\n"
            "  \"password_confirm\": \"StrongPass123\"\n"
            "}\n\n"
            "Response example (201):\n"
            "{\n"
            "  \"email\": \"alice@example.com\",\n"
            "  \"first_name\": \"Alice\",\n"
            "  \"last_name\": \"Smith\",\n"
            "  \"preferred_language\": \"en\",\n"
            "  \"tokens\": {\n"
            "    \"access\": \"<jwt-access-token>\",\n"
            "    \"refresh\": \"<jwt-refresh-token>\"\n"
            "  }\n"
            "}"
        ),
        request=RegistrationSerializer,
        responses={
            201: OpenApiResponse(
                response=RegistrationSerializer,
                description="User registered successfully.",
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponse,
                description="Validation failed (e.g., email exists or passwords do not match).",
            ),
            429: OpenApiResponse(
                response=RateLimitErrorResponse,
                description="Too many registration attempts from the same client IP.",
            ),
        },
        examples=[
            OpenApiExample(
                "Register Request",
                value={
                    "email": "alice@example.com",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "preferred_language": "en",
                    "password": "StrongPass123",
                    "password_confirm": "StrongPass123",
                },
                request_only=True,
            ),
            OpenApiExample(
                "Register Success",
                value={
                    "email": "alice@example.com",
                    "first_name": "Alice",
                    "last_name": "Smith",
                    "preferred_language": "en",
                    "tokens": {
                        "access": "<jwt-access-token>",
                        "refresh": "<jwt-refresh-token>",
                    },
                },
                response_only=True,
                status_codes=["201"],
            ),
            OpenApiExample(
                "Register Validation Error",
                value={"password": ["Passwords must match!"]},
                response_only=True,
                status_codes=["400"],
            ),
            OpenApiExample(
                "Register Rate Limit Error",
                value={"detail": "Too many requests. Try again later."},
                response_only=True,
                status_codes=["429"],
            ),
        ],
    ),
    token=extend_schema(
        tags=["Auth"],
        summary="Refresh access token using refresh token",
        description=(
            "Exchanges a valid refresh token for a new access token. "
            "Authentication header is not required; refresh token in body is required. "
            "Side effects: writes token refresh audit logs. Language behavior: validation/error "
            "messages may follow active request language. Timezone behavior: not applicable.\n\n"
            "Request example:\n"
            "POST /api/auth/token/refresh/\n"
            "{\n"
            "  \"refresh\": \"<jwt-refresh-token>\"\n"
            "}\n\n"
            "Response example (200):\n"
            "{\n"
            "  \"access\": \"<new-jwt-access-token>\"\n"
            "}"
        ),
        request=inline_serializer(
            name="TokenRefreshRequest",
            fields={"refresh": serializers.CharField()},
        ),
        responses={
            200: OpenApiResponse(
                response=inline_serializer(
                    name="TokenRefreshSuccessResponse",
                    fields={"access": serializers.CharField()},
                ),
                description="Token refreshed successfully.",
            ),
            400: OpenApiResponse(
                response=ValidationErrorResponse,
                description="Invalid or malformed refresh token payload.",
            ),
            401: OpenApiResponse(
                response=inline_serializer(
                    name="TokenRefreshUnauthorizedResponse",
                    fields={
                        "detail": serializers.CharField(),
                        "code": serializers.CharField(required=False),
                    },
                ),
                description="Refresh token is expired or invalid.",
            ),
        },
        examples=[
            OpenApiExample(
                "Token Refresh Request",
                value={"refresh": "<jwt-refresh-token>"},
                request_only=True,
            ),
            OpenApiExample(
                "Token Refresh Success",
                value={"access": "<new-jwt-access-token>"},
                response_only=True,
                status_codes=["200"],
            ),
            OpenApiExample(
                "Token Refresh Error",
                value={"detail": "Token is invalid or expired", "code": "token_not_valid"},
                response_only=True,
                status_codes=["401"],
            ),
        ],
    ),
)
class AuthViewSet(ViewSet):
    """
    ViewSet for Authentication
    """

    permission_classes = [AllowAny]

    @action(
        methods=("POST",),
        detail=False,
        url_path="token",
        url_name="token",
    )
    @ratelimit(key_func=lambda r: get_client_ip(r), rate="10/m", method="POST")
    def login(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        email = request.data.get("email", "N/A")
        logger.info(f"Login attempt: email={email}")

        serializer = LoginSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            logger.info(f"Login successful: email={email}")
            return DRFResponse(
                data=serializer.validated_data,
                status=HTTP_200_OK,
            )

        logger.warning(f"Login failed: email={email}, errors={serializer.errors}")
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=("POST",),
        detail=False,
        url_path="register",
        url_name="register",
    )
    @ratelimit(key_func=lambda r: get_client_ip(r), rate="5/m", method="POST")
    def register(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        email = request.data.get("email", "N/A")
        logger.info(f"Registration attempt: email={email}")

        serializer: RegistrationSerializer = RegistrationSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.save()
            logger.info(f"Registration successful: user_id={user.id}, email={email}")
            return DRFResponse(
                data=serializer.data,
                status=HTTP_201_CREATED,
            )
        logger.warning(
            f"Registration failed: email={email}, errors={serializer.errors}"
        )
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )

    @action(
        methods=("POST",),
        detail=False,
        url_path="token/refresh",
        url_name="refresh",
    )
    def token(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        logger.info("Token refresh attempt")
        serializer: TokenRefreshSerializer = TokenRefreshSerializer(
            data=request.data,
        )
        try:
            if serializer.is_valid():
                logger.info("Token refresh successful")
                return DRFResponse(
                    data=serializer.validated_data,
                    status=HTTP_200_OK,
                )
        except TokenError as e:
            logger.error(f"Token refresh failed: {str(e)}")
            raise InvalidToken(e.args[0])

        logger.warning(f"Token refresh validation failed: {serializer.errors}")
        return DRFResponse(
            data=serializer.errors,
            status=HTTP_400_BAD_REQUEST,
        )
