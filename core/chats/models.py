from pathlib import Path

from django.conf import settings
from django.db import models


def chat_attachment_upload_to(instance, filename):
    suffix = Path(filename).suffix.lower()
    return f"chats/conversations/{instance.message.conversation_id}/{instance.message_id}{suffix}"


class Conversation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="chat_conversations",
    )
    writer_profile = models.ForeignKey(
        "writers.WriterProfile",
        on_delete=models.CASCADE,
        related_name="chat_conversations",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-updated_at",)
        constraints = [
            models.UniqueConstraint(
                fields=("user", "writer_profile"),
                name="unique_user_writer_conversation",
            ),
        ]

    def __str__(self):
        return f"{self.user} with {self.writer_profile}"


class Message(models.Model):
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="sent_chat_messages",
    )
    text = models.TextField(blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("created_at", "id")
        indexes = [
            models.Index(fields=("conversation", "created_at")),
            models.Index(fields=("conversation", "read_at")),
        ]

    def __str__(self):
        return f"Message {self.pk} in conversation {self.conversation_id}"


class MessageAttachment(models.Model):
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="attachments",
    )
    file = models.FileField(upload_to=chat_attachment_upload_to)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=120)
    size = models.PositiveIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.original_name
