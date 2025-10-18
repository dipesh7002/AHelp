from authentication.models import (
    CommonUser,
)
from core.mixins.serializers import CommonSerializer

class CommonUserSerializer(CommonSerializer):
    class Meta(CommonSerializer.Meta):
        model = CommonUser
        fields = '__all__'