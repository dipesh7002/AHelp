from authentication.models import (
    CommonUser,
)
from core.mixins.serializers import ModelSerializer
from rest_framework.serializers import ModelSerializer, SerializerMethodField, CharField
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import AuthenticationFailed


class CommonUserSerializer(ModelSerializer):
    password = CharField(write_only=True, required=False, allow_blank=True)
    
    class Meta:
        model = CommonUser
        fields = [
            'id',
            'first_name',
            'middle_name',
            'last_name',
            'email',
            'username',
            'image',
            'is_staff',
            'is_active',
            'role',
            'email_verified',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True},
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = CommonUser.objects.create_user(**validated_data, password=password)
        
        # Send verification email if user is AssignmentHelper
        if user.role == CommonUser.Role.HELPER:
            from authentication.verification import send_verification_email
            send_verification_email(user)
        
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer that accepts email instead of username.
    """
    email = CharField(write_only=True, required=True)
    password = CharField(write_only=True, required=True)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove default username field
        self.fields.pop('username', None)

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        
        email = attrs.get('email')
        password = attrs.get('password')

        if not email or not password:
            raise AuthenticationFailed('Email and password are required')

        # Try to find and authenticate user
        try:
            user = CommonUser.objects.get(email=email)
        except CommonUser.DoesNotExist:
            raise AuthenticationFailed('Invalid email or password')
        except CommonUser.MultipleObjectsReturned:
            # This should never happen with unique constraint, but handle it
            raise AuthenticationFailed('System error - duplicate users found')

        # Verify password
        if not user.check_password(password):
            raise AuthenticationFailed('Invalid email or password')

        if not user.is_active:
            raise AuthenticationFailed('User account is inactive')

        # Generate tokens
        refresh = RefreshToken.for_user(user)
        data = {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
        return data
