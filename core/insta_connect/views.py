from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from django.shortcuts import redirect
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from .models import InstagramAccount, InstagramConversation, InstagramMessage, WebhookEvent
from .serializers import (
    InstagramAccountSerializer,
    InstagramConversationSerializer,
    InstagramConversationDetailSerializer,
    InstagramMessageSerializer,
    SendMessageSerializer,
    SendMediaMessageSerializer,
)
from .services import InstagramService, InstagramDataSync


# OAuth Flow Views

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def instagram_connect(request):
    """
    Step 1: Initiate Instagram OAuth connection
    Returns the authorization URL for the user to visit
    """
    service = InstagramService()
    redirect_uri = request.build_absolute_uri('/api/instagram/callback/')
    
    auth_url = service.get_authorization_url(redirect_uri)
    
    return Response({
        'authorization_url': auth_url,
        'message': 'Please visit this URL to connect your Instagram account'
    })


@api_view(['GET'])
def instagram_callback(request):
    """
    Step 2: Handle OAuth callback after user authorizes
    Exchange code for access token and save account details
    """
    code = request.GET.get('code')
    error = request.GET.get('error')
    
    if error:
        return Response({
            'error': 'Authorization failed',
            'details': request.GET.get('error_description', 'User denied access')
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not code:
        return Response({
            'error': 'No authorization code received'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        service = InstagramService()
        redirect_uri = request.build_absolute_uri('/api/instagram/callback/')
        
        # Exchange code for short-lived token
        short_token = service.exchange_code_for_token(code, redirect_uri)
        
        # Exchange for long-lived token
        long_token, expires_in = service.get_long_lived_token(short_token)
        
        # Get Facebook pages
        pages = service.get_facebook_pages(long_token)
        
        if not pages:
            return Response({
                'error': 'No Facebook pages found',
                'message': 'Please ensure your Instagram account is connected to a Facebook page'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Store pages info in session for user to select
        request.session['instagram_temp_token'] = long_token
        request.session['instagram_temp_expires'] = expires_in
        request.session['instagram_pages'] = [
            {'id': page['id'], 'name': page['name'], 'access_token': page['access_token']}
            for page in pages
        ]
        
        # Redirect to frontend page selection or return data
        return Response({
            'message': 'Authorization successful. Please select a Facebook page.',
            'pages': [{'id': p['id'], 'name': p['name']} for p in pages]
        })
        
    except Exception as e:
        return Response({
            'error': 'Failed to complete authorization',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def instagram_complete_connection(request):
    """
    Step 3: Complete Instagram connection by selecting a page
    This connects the Instagram Business Account to the user
    """
    page_id = request.data.get('page_id')
    
    if not page_id:
        return Response({
            'error': 'page_id is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Get stored data from session
    pages = request.session.get('instagram_pages', [])
    user_token = request.session.get('instagram_temp_token')
    expires_in = request.session.get('instagram_temp_expires')
    
    if not pages or not user_token:
        return Response({
            'error': 'Session expired. Please start the connection process again.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Find selected page
    selected_page = next((p for p in pages if p['id'] == page_id), None)
    
    if not selected_page:
        return Response({
            'error': 'Invalid page_id'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        service = InstagramService()
        
        # Get Instagram Business Account ID
        instagram_id = service.get_instagram_account(
            selected_page['id'],
            selected_page['access_token']
        )
        
        if not instagram_id:
            return Response({
                'error': 'No Instagram Business Account found',
                'message': 'Please ensure this Facebook page is connected to an Instagram Business Account'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get Instagram profile info
        profile = service.get_instagram_profile(
            instagram_id,
            selected_page['access_token']
        )
        
        # Calculate token expiry
        token_expires_at = timezone.now() + timedelta(seconds=expires_in) if expires_in else None
        
        # Save or update Instagram account
        instagram_account, created = InstagramAccount.objects.update_or_create(
            user=request.user,
            defaults={
                'instagram_business_account_id': instagram_id,
                'instagram_username': profile.get('username', ''),
                'access_token': selected_page['access_token'],
                'token_expires_at': token_expires_at,
                'facebook_page_id': selected_page['id'],
                'facebook_page_name': selected_page['name'],
                'is_active': True,
            }
        )
        
        # Subscribe to webhooks
        service.subscribe_webhook(selected_page['id'], selected_page['access_token'])
        
        # Initial sync of conversations
        sync_service = InstagramDataSync(instagram_account)
        sync_service.sync_conversations()
        
        # Clear session data
        request.session.pop('instagram_temp_token', None)
        request.session.pop('instagram_temp_expires', None)
        request.session.pop('instagram_pages', None)
        
        serializer = InstagramAccountSerializer(instagram_account)
        
        return Response({
            'message': 'Instagram account connected successfully',
            'account': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to connect Instagram account',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Account Management Views

class InstagramAccountViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing Instagram account
    """
    serializer_class = InstagramAccountSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return InstagramAccount.objects.filter(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def disconnect(self, request, pk=None):
        """
        Disconnect Instagram account
        """
        account = self.get_object()
        account.is_active = False
        account.save()
        
        return Response({
            'message': 'Instagram account disconnected successfully'
        })
    
    @action(detail=True, methods=['post'])
    def sync(self, request, pk=None):
        """
        Manually trigger sync of conversations and messages
        """
        account = self.get_object()
        
        if not account.is_token_valid():
            return Response({
                'error': 'Access token expired. Please reconnect your account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            sync_service = InstagramDataSync(account)
            conversations = sync_service.sync_conversations()
            
            return Response({
                'message': 'Sync completed successfully',
                'conversations_synced': len(conversations)
            })
        except Exception as e:
            return Response({
                'error': 'Sync failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Conversation Views

class InstagramConversationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing Instagram conversations
    """
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        try:
            instagram_account = self.request.user.instagram_account
            return InstagramConversation.objects.filter(
                instagram_account=instagram_account,
                is_archived=False
            )
        except InstagramAccount.DoesNotExist:
            return InstagramConversation.objects.none()
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return InstagramConversationDetailSerializer
        return InstagramConversationSerializer
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        """
        Mark conversation as read
        """
        conversation = self.get_object()
        conversation.is_read = True
        conversation.save()
        
        # Mark all messages as read
        conversation.messages.filter(is_read=False).update(is_read=True)
        
        return Response({'message': 'Conversation marked as read'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """
        Archive conversation
        """
        conversation = self.get_object()
        conversation.is_archived = True
        conversation.save()
        
        return Response({'message': 'Conversation archived'})


# Messaging Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_message(request):
    """
    Send a text message in a conversation
    """
    serializer = SendMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        instagram_account = request.user.instagram_account
        
        if not instagram_account.is_token_valid():
            return Response({
                'error': 'Access token expired. Please reconnect your account.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Get conversation
        conversation = InstagramConversation.objects.get(
            conversation_id=serializer.validated_data['conversation_id'],
            instagram_account=instagram_account
        )
        
        # Send message via API
        service = InstagramService()
        result = service.send_message(
            instagram_account.instagram_business_account_id,
            conversation.participant_instagram_id,
            serializer.validated_data['message_text'],
            instagram_account.access_token
        )
        
        # Create message record
        message = InstagramMessage.objects.create(
            conversation=conversation,
            message_id=result.get('message_id', ''),
            is_from_business=True,
            message_type='text',
            text=serializer.validated_data['message_text'],
            timestamp=timezone.now()
        )
        
        # Update conversation
        conversation.last_message_time = message.timestamp
        conversation.save()
        
        return Response({
            'message': 'Message sent successfully',
            'data': InstagramMessageSerializer(message).data
        }, status=status.HTTP_201_CREATED)
        
    except InstagramAccount.DoesNotExist:
        return Response({
            'error': 'Instagram account not connected'
        }, status=status.HTTP_400_BAD_REQUEST)
    except InstagramConversation.DoesNotExist:
        return Response({
            'error': 'Conversation not found'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to send message',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def send_media_message(request):
    """
    Send a media message (image/video) in a conversation
    """
    serializer = SendMediaMessageSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        instagram_account = request.user.instagram_account
        
        # Get conversation
        conversation = InstagramConversation.objects.get(
            conversation_id=serializer.validated_data['conversation_id'],
            instagram_account=instagram_account
        )
        
        # Send media message via API
        service = InstagramService()
        result = service.send_media_message(
            instagram_account.instagram_business_account_id,
            conversation.participant_instagram_id,
            serializer.validated_data['media_url'],
            serializer.validated_data['media_type'],
            instagram_account.access_token
        )
        
        # Create message record
        message = InstagramMessage.objects.create(
            conversation=conversation,
            message_id=result.get('message_id', ''),
            is_from_business=True,
            message_type=serializer.validated_data['media_type'],
            media_url=serializer.validated_data['media_url'],
            timestamp=timezone.now()
        )
        
        return Response({
            'message': 'Media sent successfully',
            'data': InstagramMessageSerializer(message).data
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': 'Failed to send media',
            'details': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)