from rest_framework.viewsets import ModelViewSet
from authentication.models import (
    CommonUser,
)
from authentication.serializers import CommonUserSerializer


class CommonUserViewset(ModelViewSet):
    queryset = CommonUser.objects.all()
    serializer_class = CommonUserSerializer
