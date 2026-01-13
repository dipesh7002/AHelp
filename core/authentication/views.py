from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny


from authentication.models import (
    CommonUser,
)
from authentication.serializers import CommonUserSerializer


class CommonUserViewset(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = CommonUser.objects.all()
    serializer_class = CommonUserSerializer
