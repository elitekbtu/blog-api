# Third-party modules
from rest_framework.serializers import ModelSerializer

# Project modules
from apps.users.models import CustomUser


class CustomUserSerializer(ModelSerializer):
    class Meta:
        model = CustomUser
        fields = "__all__"
