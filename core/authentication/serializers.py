from authentication.models import (
    CommonUser,
)
from core.mixins.serializers import ModelSerializer
from rest_framework.serializers import ModelSerializer
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CommonUserSerializer(ModelSerializer):
    class Meta:
        model = CommonUser
        fields = "__all__"


# class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
#     pass
    # username_field = 'email'
    
    # def __init__(self, *args, **kwargs):
    #     super().__init__(*args, **kwargs)
    #     self.fields['email'] = self.fields.pop('username')
