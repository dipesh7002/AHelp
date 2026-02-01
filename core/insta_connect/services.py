import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone
from .models import InstagramAccount, InstagramConversation, InstagramMessage


class InstagramService:
    """
    Service class to interact with Instagram Graph API
    """

    def __init__(self):
        # Get credentials from database instead of Django settings
        from settings.models import InstagramSettings
        instagram_settings = InstagramSettings.objects.first()

        if instagram_settings:
            self.api_url = instagram_settings.graph_api_url
            self.app_id = instagram_settings.app_id
            self.app_secret = instagram_settings.app_secret
            self.api_version = instagram_settings.api_version
        else:
            # Fallback to settings if database is not configured
            self.api_url = getattr(settings, 'INSTAGRAM_GRAPH_API_URL', 'https://graph.facebook.com/v20.0')
            self.app_id = getattr(settings, 'INSTAGRAM_APP_ID', '')
            self.app_secret = getattr(settings, 'INSTAGRAM_APP_SECRET', '')
            self.api_version = getattr(settings, 'INSTAGRAM_API_VERSION', 'v20.0')
    
    def get_authorization_url(self, redirect_uri):
        """
        Step 1: Generate OAuth URL for user to authorize
        User clicks this URL to connect their Instagram account
        """
        from settings.models import InstagramSettings
        instagram_settings = InstagramSettings.objects.first()

        if instagram_settings:
            permissions = ','.join(instagram_settings.permissions)
            api_version = instagram_settings.api_version
        else:
            # Fallback permissions
            permissions = ','.join([
                'pages_messaging',
                'pages_show_list',
                'instagram_basic',
                'instagram_manage_messages',
                'instagram_manage_comments'
            ])
            api_version = self.api_version

        auth_url = (
            f"https://www.facebook.com/{api_version}/dialog/oauth?"
            f"client_id={self.app_id}"
            f"&redirect_uri={redirect_uri}"
            f"&scope={permissions}"
            f"&response_type=code"
        )

        return auth_url
    
    def exchange_code_for_token(self, code, redirect_uri):
        """
        Step 2: Exchange authorization code for access token
        Called after user authorizes and returns to callback URL
        """
        token_url = f"{self.api_url}/oauth/access_token"
        
        params = {
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'redirect_uri': redirect_uri,
            'code': code,
        }
        
        response = requests.get(token_url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('access_token')
    
    def get_long_lived_token(self, short_lived_token):
        """
        Step 3: Exchange short-lived token for long-lived token (60 days)
        """
        url = f"{self.api_url}/oauth/access_token"
        
        params = {
            'grant_type': 'fb_exchange_token',
            'client_id': self.app_id,
            'client_secret': self.app_secret,
            'fb_exchange_token': short_lived_token,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('access_token'), data.get('expires_in')
    
    def get_facebook_pages(self, access_token):
        """
        Step 4: Get user's Facebook Pages
        """
        url = f"{self.api_url}/me/accounts"
        
        params = {
            'access_token': access_token,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('data', [])
    
    def get_instagram_account(self, page_id, access_token):
        """
        Step 5: Get Instagram Business Account connected to Facebook Page
        """
        url = f"{self.api_url}/{page_id}"
        
        params = {
            'fields': 'instagram_business_account',
            'access_token': access_token,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return data.get('instagram_business_account', {}).get('id')
    
    def get_instagram_profile(self, instagram_account_id, access_token):
        """
        Get Instagram account profile information
        """
        url = f"{self.api_url}/{instagram_account_id}"
        
        params = {
            'fields': 'username,name,profile_picture_url',
            'access_token': access_token,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json()
    
    def get_conversations(self, instagram_account_id, access_token, limit=20):
        """
        Fetch conversations (message threads) for the Instagram account
        """
        url = f"{self.api_url}/{instagram_account_id}/conversations"
        
        params = {
            'fields': 'id,participants,updated_time,messages.limit(1){message,from,created_time}',
            'access_token': access_token,
            'limit': limit,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('data', [])
    
    def get_conversation_messages(self, conversation_id, access_token, limit=50):
        """
        Fetch all messages in a specific conversation
        """
        url = f"{self.api_url}/{conversation_id}"
        
        params = {
            'fields': 'messages{id,message,from,created_time,attachments}',
            'access_token': access_token,
        }
        
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return response.json().get('messages', {}).get('data', [])
    
    def send_message(self, instagram_account_id, recipient_id, message_text, access_token):
        """
        Send a text message to a user
        
        Args:
            instagram_account_id: Your Instagram Business Account ID
            recipient_id: Instagram Scoped ID of the recipient
            message_text: Text message to send
            access_token: Page access token
        """
        url = f"{self.api_url}/{instagram_account_id}/messages"
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'text': message_text},
            'access_token': access_token,
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def send_media_message(self, instagram_account_id, recipient_id, media_url, 
                          media_type, access_token):
        """
        Send a media message (image/video)
        
        Args:
            media_type: 'image' or 'video'
        """
        url = f"{self.api_url}/{instagram_account_id}/messages"
        
        attachment = {
            'type': media_type,
            'payload': {'url': media_url}
        }
        
        payload = {
            'recipient': {'id': recipient_id},
            'message': {'attachment': attachment},
            'access_token': access_token,
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def mark_as_read(self, conversation_id, access_token):
        """
        Mark a conversation as read
        """
        url = f"{self.api_url}/{conversation_id}"
        
        payload = {
            'access_token': access_token,
        }
        
        response = requests.post(url, json=payload)
        response.raise_for_status()
        
        return response.json()
    
    def subscribe_webhook(self, page_id, access_token):
        """
        Subscribe the page to receive webhook notifications
        """
        url = f"{self.api_url}/{page_id}/subscribed_apps"
        
        params = {
            'subscribed_fields': 'messages,messaging_postbacks,message_echoes',
            'access_token': access_token,
        }
        
        response = requests.post(url, params=params)
        response.raise_for_status()
        
        return response.json()


class InstagramDataSync:
    """
    Service to sync Instagram data with local database
    """
    
    def __init__(self, instagram_account):
        self.instagram_account = instagram_account
        self.service = InstagramService()
    
    def sync_conversations(self):
        """
        Fetch and sync all conversations
        """
        conversations_data = self.service.get_conversations(
            self.instagram_account.instagram_business_account_id,
            self.instagram_account.access_token
        )
        
        synced_conversations = []
        
        for conv_data in conversations_data:
            conversation = self._sync_conversation(conv_data)
            synced_conversations.append(conversation)
        
        self.instagram_account.last_sync = timezone.now()
        self.instagram_account.save()
        
        return synced_conversations
    
    def _sync_conversation(self, conv_data):
        """
        Sync a single conversation
        """
        # Get participant info
        participants = conv_data.get('participants', {}).get('data', [])
        participant = next(
            (p for p in participants if p['id'] != self.instagram_account.instagram_business_account_id),
            None
        )
        
        if not participant:
            return None
        
        # Create or update conversation
        conversation, created = InstagramConversation.objects.update_or_create(
            conversation_id=conv_data['id'],
            defaults={
                'instagram_account': self.instagram_account,
                'participant_instagram_id': participant['id'],
                'participant_username': participant.get('username', ''),
                'participant_name': participant.get('name', ''),
                'updated_at': timezone.now(),
            }
        )
        
        # Sync messages for this conversation
        self.sync_conversation_messages(conversation)
        
        return conversation
    
    def sync_conversation_messages(self, conversation):
        """
        Sync all messages for a conversation
        """
        messages_data = self.service.get_conversation_messages(
            conversation.conversation_id,
            self.instagram_account.access_token
        )
        
        for msg_data in messages_data:
            self._sync_message(conversation, msg_data)
        
        # Update last message time
        last_message = conversation.messages.order_by('-timestamp').first()
        if last_message:
            conversation.last_message_time = last_message.timestamp
            conversation.save()
    
    def _sync_message(self, conversation, msg_data):
        """
        Sync a single message
        """
        # Determine if message is from business
        is_from_business = msg_data.get('from', {}).get('id') == self.instagram_account.instagram_business_account_id
        
        # Get message content
        message_text = msg_data.get('message', '')
        
        # Handle attachments
        attachments = msg_data.get('attachments', {}).get('data', [])
        media_url = ''
        message_type = 'text'
        
        if attachments:
            attachment = attachments[0]
            message_type = attachment.get('type', 'unsupported')
            if message_type in ['image', 'video', 'audio']:
                media_url = attachment.get('url', '')
        
        # Create or update message
        message, created = InstagramMessage.objects.update_or_create(
            message_id=msg_data['id'],
            defaults={
                'conversation': conversation,
                'is_from_business': is_from_business,
                'message_type': message_type,
                'text': message_text,
                'media_url': media_url,
                'timestamp': msg_data.get('created_time'),
            }
        )
        
        return message