from authentication.models import (
    CommonUser,
)
from core.mixins.serializers import ModelSerializer
from rest_framework.serializers import ModelSerializer


class CommonUserSerializer(ModelSerializer):
    class Meta:
        model = CommonUser
        fields = "__all__"
