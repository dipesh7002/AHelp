from django.db import models
from authentication.models import CommonUser
from helper.models import AssignmentHelper
from django.utils.translation import gettext_lazy as _


class Conversation(models.Model):
    """
    Represents a conversation between two users.
    Can be between CommonUser and AssignmentHelper, or SuperUser and anyone.
    """
    participant1 = models.ForeignKey(
        CommonUser, 
        on_delete=models.CASCADE, 
        related_name="conversations_as_participant1",
        verbose_name=_("Participant 1")
    )
    participant2 = models.ForeignKey(
        CommonUser, 
        on_delete=models.CASCADE, 
        related_name="conversations_as_participant2",
        verbose_name=_("Participant 2")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Updated At"))

    class Meta:
        unique_together = ['participant1', 'participant2']
        ordering = ['-updated_at']

    def __str__(self):
        return f"Conversation({self.participant1.email} <-> {self.participant2.email})"

    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        if self.participant1 == user:
            return self.participant2
        return self.participant1

    def has_participant(self, user):
        """Check if user is a participant in this conversation"""
        return self.participant1 == user or self.participant2 == user


class Message(models.Model):
    """
    Represents a message in a conversation.
    """
    conversation = models.ForeignKey(
        Conversation, 
        on_delete=models.CASCADE, 
        related_name="messages",
        verbose_name=_("Conversation")
    )
    sender = models.ForeignKey(
        CommonUser, 
        on_delete=models.CASCADE, 
        related_name="sent_messages",
        verbose_name=_("Sender")
    )
    receiver = models.ForeignKey(
        CommonUser, 
        on_delete=models.CASCADE, 
        related_name="received_messages",
        verbose_name=_("Receiver")
    )
    text = models.TextField(max_length=5000, verbose_name=_("Message Text"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Created At"))
    is_read = models.BooleanField(default=False, verbose_name=_("Is Read"))

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Message({self.sender.email} -> {self.receiver.email})"


# Keep Room model for backward compatibility if needed
class Room(models.Model):
    name = models.CharField(max_length=255, null=False, blank=False, unique=True)
    current_users = models.ManyToManyField(
        CommonUser, related_name="current_rooms", blank=True
    )

    def __str__(self):
        return f"Room({self.name})"
