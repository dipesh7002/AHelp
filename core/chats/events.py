from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def user_group_name(user_id):
    return f"chat_user_{user_id}"


def broadcast_to_user(user_id, event_type, payload):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        user_group_name(user_id),
        {
            "type": "chat.event",
            "event": event_type,
            "payload": payload,
        },
    )


def broadcast_conversation_event(conversation, event_type, payload):
    participant_ids = {conversation.user_id, conversation.writer_profile.user_id}
    for user_id in participant_ids:
        broadcast_to_user(user_id, event_type, payload)
