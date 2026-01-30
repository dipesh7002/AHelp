from django.db import models
from authentication.models import CommonUser, CommonModel

class InstagramAccount(CommonModel):
    user = models.OneToOneField(CommonUser,
                                on_delete=models.CASCADE, 
                                related_name='instagram_account',
                                ) 
    instagram_business_account_id = models.CharField(max_length=255, unique=True)
    instagram_username = models.CharField(max_length=255)
    access_token = models.TextField()
    token_expires_at = models.DateTimeField(null=True, blank=True)
    
    facebook_page_id = models.CharField(max_length=255)
    facebook_page_name = models.CharField(max_length=255, blank=True)
    
    class Meta:
        db_table = 'instagram_accounts'
        verbose_name = 'Instagram Account'
        verbose_name_plural = 'Instagram Accounts'
        
    def __str__(self):
        return f"{self.user.first_name} - @{self.instagram_username}" 
    
class InstagramConversation(CommonModel):
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='conversations'
    )
    
    conversation_id = models.CharField(max_length=255, unique=True)
    participant_instagram_id = models.CharField(max_length=255)
    participant_username = models.CharField(max_length=255, blank=True)
    participant_name = models.CharField(max_length=255, blank=True)
    participant_profile_pic = models.URLField(blank=True)
    
    # Conversation metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_message_time = models.DateTimeField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'instagram_conversations'
        ordering = ['-last_message_time']
        indexes = [
            models.Index(fields=['instagram_account', '-last_message_time']),
            models.Index(fields=['conversation_id']),
        ]
    
    def __str__(self):
        return f"Conversation with @{self.participant_username}"


class InstagramMessage(models.Model):
    """
    Stores individual messages in a conversation
    """
    MESSAGE_TYPES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('story_mention', 'Story Mention'),
        ('story_reply', 'Story Reply'),
        ('reel_share', 'Reel Share'),
        ('like', 'Like'),
        ('unsupported', 'Unsupported'),
    )
    
    conversation = models.ForeignKey(
        InstagramConversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    
    # Message details
    message_id = models.CharField(max_length=255, unique=True)
    
    # Direction
    is_from_business = models.BooleanField(default=False)  # True if sent by business
    
    # Content
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPES, default='text')
    text = models.TextField(blank=True)
    media_url = models.URLField(blank=True)
    
    # Metadata
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        db_table = 'instagram_messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['message_id']),
        ]
    
    def __str__(self):
        direction = "→" if self.is_from_business else "←"
        return f"{direction} {self.text[:50]}"


class WebhookEvent(models.Model):
    """
    Logs all webhook events for debugging and audit
    """
    instagram_account = models.ForeignKey(
        InstagramAccount,
        on_delete=models.CASCADE,
        related_name='webhook_events',
        null=True,
        blank=True
    )
    
    event_type = models.CharField(max_length=100)
    raw_data = models.JSONField()
    processed = models.BooleanField(default=False)
    error_message = models.TextField(blank=True)
    
    received_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'webhook_events'
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['processed', 'received_at']),
        ]
    
    def __str__(self):
        return f"{self.event_type} - {self.received_at}"
