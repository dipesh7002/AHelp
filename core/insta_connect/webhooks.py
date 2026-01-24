import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone

from .models import InstagramAccount, InstagramConversation, InstagramMessage, WebhookEvent


@csrf_exempt
@require_http_methods(["GET", "POST"])
def instagram_webhook(request):
    """
    Instagram Webhook endpoint
    
    GET: Webhook verification (one-time setup)
    POST: Receive webhook events (messages, etc.)
    """
    
    if request.method == 'GET':
        return verify_webhook(request)
    elif request.method == 'POST':
        return handle_webhook(request)


def verify_webhook(request):
    """
    Webhook verification for initial setup
    
    Facebook/Instagram sends:
    - hub.mode: 'subscribe'
    - hub.verify_token: your verification token
    - hub.challenge: random string to echo back
    """
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    
    verify_token = settings.INSTAGRAM_WEBHOOK_VERIFY_TOKEN
    
    if mode == 'subscribe' and token == verify_token:
        # Respond with challenge to verify webhook
        return HttpResponse(challenge, content_type='text/plain')
    else:
        return HttpResponse('Verification failed', status=403)


def handle_webhook(request):
    """
    Handle incoming webhook events
    
    Instagram sends events when:
    - New message received
    - Message delivered
    - Message read
    - User interaction (like, reaction, etc.)
    """
    try:
        # Parse webhook payload
        data = json.loads(request.body.decode('utf-8'))
        
        # Process each entry
        for entry in data.get('entry', []):
            # Get page/account ID
            page_id = entry.get('id')
            
            # Process messaging events
            messaging_events = entry.get('messaging', [])
            
            for event in messaging_events:
                process_messaging_event(page_id, event)
        
        # Always return 200 OK to acknowledge receipt
        return HttpResponse('EVENT_RECEIVED', status=200)
        
    except Exception as e:
        # Log error but still return 200 to prevent retries
        print(f"Webhook error: {str(e)}")
        return HttpResponse('ERROR', status=200)


def process_messaging_event(page_id, event):
    """
    Process a single messaging event
    """
    try:
        # Find Instagram account by page ID
        instagram_account = InstagramAccount.objects.filter(
            facebook_page_id=page_id,
            is_active=True
        ).first()
        
        if not instagram_account:
            # Log event for unknown account
            WebhookEvent.objects.create(
                event_type='unknown_account',
                raw_data=event,
                processed=False,
                error_message=f'No active account found for page {page_id}'
            )
            return
        
        # Determine event type
        if 'message' in event:
            handle_message_event(instagram_account, event)
        elif 'read' in event:
            handle_read_event(instagram_account, event)
        elif 'delivery' in event:
            handle_delivery_event(instagram_account, event)
        
        # Log successful processing
        WebhookEvent.objects.create(
            instagram_account=instagram_account,
            event_type='message' if 'message' in event else 'other',
            raw_data=event,
            processed=True,
            processed_at=timezone.now()
        )
        
    except Exception as e:
        # Log failed event
        WebhookEvent.objects.create(
            event_type='processing_error',
            raw_data=event,
            processed=False,
            error_message=str(e)
        )


def handle_message_event(instagram_account, event):
    """
    Handle incoming message event
    """
    sender = event.get('sender', {})
    recipient = event.get('recipient', {})
    message_data = event.get('message', {})
    timestamp = event.get('timestamp')
    
    # Determine if this is an echo (message sent by business)
    is_echo = message_data.get('is_echo', False)
    
    # Get sender/recipient IDs
    sender_id = sender.get('id')
    recipient_id = recipient.get('id')
    
    # Determine conversation participant (the customer)
    if is_echo:
        # Business sent this message, participant is recipient
        participant_id = recipient_id
        is_from_business = True
    else:
        # Customer sent this message, participant is sender
        participant_id = sender_id
        is_from_business = False
    
    # Skip if participant is the business itself
    if participant_id == instagram_account.instagram_business_account_id:
        return
    
    # Get or create conversation
    # Note: We need the actual conversation_id from Instagram
    # For webhooks, we might need to fetch it via API or use a composite key
    conversation_id = f"{instagram_account.instagram_business_account_id}_{participant_id}"
    
    conversation, created = InstagramConversation.objects.get_or_create(
        instagram_account=instagram_account,
        participant_instagram_id=participant_id,
        defaults={
            'conversation_id': conversation_id,
        }
    )
    
    # Extract message content
    message_text = message_data.get('text', '')
    message_id = message_data.get('mid')
    
    # Handle attachments
    attachments = message_data.get('attachments', [])
    media_url = ''
    message_type = 'text'
    
    if attachments:
        attachment = attachments[0]
        attachment_type = attachment.get('type')
        
        if attachment_type == 'image':
            message_type = 'image'
            media_url = attachment.get('payload', {}).get('url', '')
        elif attachment_type == 'video':
            message_type = 'video'
            media_url = attachment.get('payload', {}).get('url', '')
        elif attachment_type == 'audio':
            message_type = 'audio'
            media_url = attachment.get('payload', {}).get('url', '')
        else:
            message_type = 'unsupported'
    
    # Create message
    message, msg_created = InstagramMessage.objects.get_or_create(
        message_id=message_id,
        defaults={
            'conversation': conversation,
            'is_from_business': is_from_business,
            'message_type': message_type,
            'text': message_text,
            'media_url': media_url,
            'timestamp': timezone.datetime.fromtimestamp(timestamp / 1000, tz=timezone.utc),
        }
    )
    
    # Update conversation
    if msg_created:
        conversation.last_message_time = message.timestamp
        if not is_from_business:
            conversation.is_read = False
        conversation.save()


def handle_read_event(instagram_account, event):
    """
    Handle message read event
    """
    # Mark messages as read
    watermark = event.get('read', {}).get('watermark')
    sender_id = event.get('sender', {}).get('id')
    
    # Find conversation
    try:
        conversation = InstagramConversation.objects.get(
            instagram_account=instagram_account,
            participant_instagram_id=sender_id
        )
        
        # Mark messages up to watermark as read
        if watermark:
            timestamp = timezone.datetime.fromtimestamp(watermark / 1000, tz=timezone.utc)
            conversation.messages.filter(
                timestamp__lte=timestamp,
                is_from_business=True
            ).update(is_read=True)
            
    except InstagramConversation.DoesNotExist:
        pass


def handle_delivery_event(instagram_account, event):
    """
    Handle message delivery event
    """
    # You can track delivery status if needed
    # For now, we'll just log it
    pass