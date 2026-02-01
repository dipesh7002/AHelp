from .models import Room, Message, Conversation
from authentication.serializers import CommonUserSerializer
from authentication.models import CommonUser
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommonUser
        exclude = ["password"]


class MessageSerializer(serializers.ModelSerializer):
    created_at_formatted = serializers.SerializerMethodField()
    sender = CommonUserSerializer(read_only=True)
    receiver = CommonUserSerializer(read_only=True)
    sender_id = serializers.IntegerField(write_only=True, required=False)
    receiver_id = serializers.IntegerField(write_only=True, required=False)

    class Meta:
        model = Message
        fields = [
            "id", "conversation", "sender", "receiver", 
            "sender_id", "receiver_id", "text", 
            "created_at", "created_at_formatted", "is_read"
        ]
        read_only_fields = ["sender", "receiver", "created_at", "is_read"]

    def get_created_at_formatted(self, obj: Message):
        return obj.created_at.strftime("%d-%m-%Y %H:%M:%S")

    def create(self, validated_data):
        sender_id = validated_data.pop('sender_id', None)
        receiver_id = validated_data.pop('receiver_id', None)
        
        if sender_id:
            validated_data['sender_id'] = sender_id
        if receiver_id:
            validated_data['receiver_id'] = receiver_id
        
        return super().create(validated_data)


class ConversationListSerializer(serializers.ModelSerializer):
    """Serializer for conversation list views (excludes messages for performance)"""
    participant1 = CommonUserSerializer(read_only=True)
    participant2 = CommonUserSerializer(read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "participant1", "participant2",
            "created_at", "updated_at",
            "last_message"
        ]

    def get_last_message(self, obj):
        # Use annotated fields from the queryset
        if hasattr(obj, 'last_message_text') and obj.last_message_text:
            return {
                "text": obj.last_message_text,
                "created_at": obj.last_message_created_at
            }
        return None


class ConversationSerializer(serializers.ModelSerializer):
    """Full serializer for conversation detail views (includes messages)"""
    participant1 = CommonUserSerializer(read_only=True)
    participant2 = CommonUserSerializer(read_only=True)
    participant1_id = serializers.IntegerField(write_only=True, required=False)
    participant2_id = serializers.IntegerField(write_only=True, required=False)
    last_message = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = [
            "id", "participant1", "participant2",
            "participant1_id", "participant2_id",
            "created_at", "updated_at",
            "last_message", "messages", "unread_count"
        ]
        read_only_fields = ["participant1", "participant2", "created_at", "updated_at"]

    def get_last_message(self, obj: Conversation):
        last_msg = obj.messages.order_by("-created_at").first()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None

    def get_unread_count(self, obj: Conversation):
        request = self.context.get('request')
        if request and request.user:
            return obj.messages.filter(receiver=request.user, is_read=False).count()
        return 0


# Keep Room serializer for backward compatibility
class RoomSerializer(serializers.ModelSerializer):
    last_message = serializers.SerializerMethodField()
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = Room
        fields = ["pk", "name", "messages", "current_users", "last_message"]
        depth = 1
        read_only_fields = ["messages", "last_message"]

    def get_last_message(self, obj: Room):
        last_msg = obj.messages.order_by("created_at").last()
        if last_msg:
            return MessageSerializer(last_msg).data
        return None
