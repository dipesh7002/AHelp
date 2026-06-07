from pathlib import Path

from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Conversation, Message, MessageAttachment
from .presence import is_online

User = get_user_model()


class UserSummarySerializer(serializers.ModelSerializer):
    profile_picture = serializers.SerializerMethodField()
    is_online = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "email", "full_name", "profile_picture", "role", "last_seen_at", "is_online")

    def get_profile_picture(self, obj):
        if not obj.profile_picture:
            return None
        request = self.context.get("request")
        url = obj.profile_picture.url
        return request.build_absolute_uri(url) if request else url

    def get_is_online(self, obj):
        return is_online(obj.id)


class AttachmentSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()

    class Meta:
        model = MessageAttachment
        fields = ("id", "original_name", "content_type", "size", "download_url")

    def get_download_url(self, obj):
        request = self.context.get("request")
        path = f"/api/chats/attachments/{obj.id}/download/"
        return request.build_absolute_uri(path) if request else path


class MessageSerializer(serializers.ModelSerializer):
    sender = UserSummarySerializer(read_only=True)
    attachments = AttachmentSerializer(many=True, read_only=True)
    is_mine = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            "id",
            "conversation",
            "sender",
            "text",
            "attachments",
            "is_mine",
            "delivered_at",
            "read_at",
            "created_at",
        )

    def get_is_mine(self, obj):
        request = self.context.get("request")
        return bool(request and request.user.is_authenticated and obj.sender_id == request.user.id)


class ConversationSerializer(serializers.ModelSerializer):
    user = UserSummarySerializer(read_only=True)
    writer = serializers.SerializerMethodField()
    writer_profile_id = serializers.IntegerField(read_only=True)
    last_message = serializers.SerializerMethodField()
    unread_count = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            "id",
            "user",
            "writer",
            "writer_profile_id",
            "last_message",
            "unread_count",
            "created_at",
            "updated_at",
        )

    def get_writer(self, obj):
        return UserSummarySerializer(obj.writer_profile.user, context=self.context).data

    def get_last_message(self, obj):
        message = getattr(obj, "_last_message", None)
        if message is None:
            message = obj.messages.select_related("sender").prefetch_related("attachments").last()
        return MessageSerializer(message, context=self.context).data if message else None

    def get_unread_count(self, obj):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return 0
        if getattr(request.user, "role", None) == User.Role.ADMIN:
            return obj.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()
        return obj.messages.filter(read_at__isnull=True).exclude(sender=request.user).count()


ALLOWED_ATTACHMENT_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".pdf", ".docx"}
ALLOWED_ATTACHMENT_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/webp",
    "image/gif",
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}
MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024
MAX_ATTACHMENTS_PER_MESSAGE = 5


def validate_chat_attachment(uploaded_file):
    extension = Path(uploaded_file.name).suffix.lower()
    content_type = getattr(uploaded_file, "content_type", "") or ""
    if extension not in ALLOWED_ATTACHMENT_EXTENSIONS:
        raise serializers.ValidationError(
            f"{uploaded_file.name} is not an allowed file type."
        )
    if content_type and content_type not in ALLOWED_ATTACHMENT_CONTENT_TYPES:
        raise serializers.ValidationError(
            f"{uploaded_file.name} has an unsupported content type."
        )
    if uploaded_file.size > MAX_ATTACHMENT_SIZE:
        raise serializers.ValidationError(
            f"{uploaded_file.name} must be 10 MB or smaller."
        )
