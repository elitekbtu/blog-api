# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework.permissions import AllowAny
from rest_framework.response import Response as DRFResponse
from rest_framework.request import Request as DRFRequest
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.decorators import action

from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken


# Project modules
from apps.users.auth.serializers import RegistrationSerializer, LoginSerializer

logger = logging.getLogger(__name__)


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
        logger.warning(f"Registration failed: email={email}, errors={serializer.errors}")
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
