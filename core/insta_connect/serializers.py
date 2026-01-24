from rest_framework import serializers
from .models import InstagramAccount, InstagramConversation, InstagramMessage


class InstagramAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram Account
    """
    is_connected = serializers.SerializerMethodField()
    token_status = serializers.SerializerMethodField()
    
    class Meta:
        model = InstagramAccount
        fields = [
            'id',
            'instagram_business_account_id',
            'instagram_username',
            'facebook_page_name',
            'is_active',
            'is_connected',
            'token_status',
            'connected_at',
            'last_sync',
        ]
        read_only_fields = ['id', 'connected_at']
    
    def get_is_connected(self, obj):
        return obj.is_active and obj.is_token_valid()
    
    def get_token_status(self, obj):
        if obj.is_token_valid():
            return 'valid'
        return 'expired'


class InstagramMessageSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram Message
    """
    sender_type = serializers.SerializerMethodField()
    formatted_time = serializers.SerializerMethodField()
    
    class Meta:
        model = InstagramMessage
        fields = [
            'id',
            'message_id',
            'is_from_business',
            'sender_type',
            'message_type',
            'text',
            'media_url',
            'timestamp',
            'formatted_time',
            'is_read',
            'is_deleted',
        ]
        read_only_fields = ['id', 'message_id', 'timestamp']
    
    def get_sender_type(self, obj):
        return 'business' if obj.is_from_business else 'customer'
    
    def get_formatted_time(self, obj):
        return obj.timestamp.strftime('%Y-%m-%d %H:%M:%S') if obj.timestamp else None


class InstagramConversationSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram Conversation (list view)
    """
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()
    
    class Meta:
        model = InstagramConversation
        fields = [
            'id',
            'conversation_id',
            'participant_instagram_id',
            'participant_username',
            'participant_name',
            'participant_profile_pic',
            'last_message',
            'last_message_time',
            'unread_count',
            'is_read',
            'is_archived',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'conversation_id', 'created_at', 'updated_at']
    
    def get_last_message(self, obj):
        last_msg = obj.messages.order_by('-timestamp').first()
        if last_msg:
            return {
                'text': last_msg.text,
                'timestamp': last_msg.timestamp,
                'is_from_business': last_msg.is_from_business,
                'message_type': last_msg.message_type,
            }
        return None
    
    def get_unread_count(self, obj):
        return obj.messages.filter(is_read=False, is_from_business=False).count()


class InstagramConversationDetailSerializer(serializers.ModelSerializer):
    """
    Serializer for Instagram Conversation (detail view with messages)
    """
    messages = InstagramMessageSerializer(many=True, read_only=True)
    participant = serializers.SerializerMethodField()
    
    class Meta:
        model = InstagramConversation
        fields = [
            'id',
            'conversation_id',
            'participant',
            'messages',
            'last_message_time',
            'is_read',
            'is_archived',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'conversation_id', 'created_at', 'updated_at']
    
    def get_participant(self, obj):
        return {
            'instagram_id': obj.participant_instagram_id,
            'username': obj.participant_username,
            'name': obj.participant_name,
            'profile_pic': obj.participant_profile_pic,
        }


class SendMessageSerializer(serializers.Serializer):
    """
    Serializer for sending a message
    """
    conversation_id = serializers.CharField(required=True)
    message_text = serializers.CharField(required=True, max_length=1000)
    
    def validate_message_text(self, value):
        if not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()


class SendMediaMessageSerializer(serializers.Serializer):
    """
    Serializer for sending a media message
    """
    conversation_id = serializers.CharField(required=True)
    media_url = serializers.URLField(required=True)
    media_type = serializers.ChoiceField(
        choices=['image', 'video'],
        required=True
    )


class InstagramConnectionSerializer(serializers.Serializer):
    """
    Serializer for initiating Instagram connection
    """
    page_id = serializers.CharField(required=True)
    
    def validate_page_id(self, value):
        if not value.strip():
            raise serializers.ValidationError("Page ID is required")
        return value.strip()