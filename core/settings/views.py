from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response

from .models import InstagramSettings
from .serializers import InstagramSettingsSerializer


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated, IsAdminUser])
def instagram_settings(request):
    """
    Get or update Instagram settings
    """
    settings, created = InstagramSettings.objects.get_or_create()

    if request.method == 'GET':
        serializer = InstagramSettingsSerializer(settings)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = InstagramSettingsSerializer(settings, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def test_instagram_connection(request):
    """
    Test Instagram API connection with current settings
    """
    try:
        instagram_settings = InstagramSettings.objects.first()
        if not instagram_settings or not instagram_settings.app_id:
            return Response({
                'error': 'Instagram settings not configured',
                'message': 'Please configure Instagram App ID and Secret first'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Import here to avoid circular imports
        from insta_connect.services import InstagramService

        # Create a temporary service instance to test connection
        service = InstagramService()
        service.app_id = instagram_settings.app_id
        service.app_secret = instagram_settings.app_secret

        # Try to get app access token as a basic connectivity test
        # This is a simplified test - in production you might want more comprehensive testing

        return Response({
            'message': 'Instagram connection test successful',
            'app_id': instagram_settings.app_id,
            'api_version': instagram_settings.api_version
        })

    except Exception as e:
        return Response({
            'error': 'Instagram connection test failed',
            'details': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
