# Python modules
from typing import Any
import logging

# Third-party modules
from rest_framework.viewsets import ViewSet
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request as DRFRequest
from rest_framework.response import Response as DRFResponse
from rest_framework.status import HTTP_200_OK

# Project modules
from apps.users.serializers import CustomUserSerializer

logger = logging.getLogger(__name__)


class CustomUserViewSet(ViewSet):
    @action(
        methods=("GET",),
        detail=False,
        url_path="profile",
        url_name="profile",
        permission_classes=(IsAuthenticated,),
    )
    def profile(
        self,
        request: DRFRequest,
        *args: tuple[Any, ...],
        **kwargs: dict[str, Any],
    ) -> DRFResponse:
        logger.info(f"Profile request by user_id={request.user.id}")
        serializer: CustomUserSerializer = CustomUserSerializer(instance=request.user)
        logger.debug(f"Profile data retrieved for user_id={request.user.id}")

        return DRFResponse(
            serializer.data,
            status=HTTP_200_OK,
        )

    # TODO: could be contuned ..
