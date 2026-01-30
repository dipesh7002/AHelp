from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework import status
from rest_framework_simplejwt.views import TokenObtainPairView

from authentication.models import (
    CommonUser,
)
from authentication.serializers import (
    CommonUserSerializer,
    CustomTokenObtainPairSerializer,
)
from authentication.verification import send_verification_email, verify_email_token


class CommonUserViewset(ModelViewSet):
    permission_classes = [AllowAny]
    queryset = CommonUser.objects.all()
    serializer_class = CommonUserSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        """Change password for the authenticated user"""
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response(
                {'error': 'Both old_password and new_password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if not user.check_password(old_password):
            return Response(
                {'error': 'Old password is incorrect'},
                status=status.HTTP_400_BAD_REQUEST
            )

        user.set_password(new_password)
        user.save()
        return Response(
            {'message': 'Password changed successfully'},
            status=status.HTTP_200_OK
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        
        if response.status_code == 200:
            # Get user from email
            email = request.data.get('email')
            try:
                user = CommonUser.objects.get(email=email)
                # Add role to response for frontend routing
                response.data['role'] = user.role
                response.data['email_verified'] = user.email_verified
            except CommonUser.DoesNotExist:
                pass
        
        return response


class VerifyEmailView(APIView):
    """Verify email for AssignmentHelper"""
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        token = request.data.get('token')
        
        if not email or not token:
            return Response(
                {'error': 'Email and token are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, user = verify_email_token(email, token)
        
        if success:
            return Response({
                'message': 'Email verified successfully',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Invalid verification token'},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResendVerificationEmailView(APIView):
    """Resend verification email"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user = request.user
        
        if user.role != CommonUser.Role.HELPER:
            return Response(
                {'error': 'Only AssignmentHelpers can request verification'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        if user.email_verified:
            return Response(
                {'message': 'Email already verified'},
                status=status.HTTP_200_OK
            )
        
        success = send_verification_email(user)
        
        if success:
            return Response({
                'message': 'Verification email sent successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(
            {'error': 'Failed to send verification email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
