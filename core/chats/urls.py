from django.urls import path

from .views import (
    AttachmentDownloadView,
    ConversationListCreateView,
    ConversationMessagesView,
    ConversationReadView,
)

urlpatterns = [
    path("conversations/", ConversationListCreateView.as_view(), name="chat-conversation-list-create"),
    path(
        "conversations/<int:pk>/messages/",
        ConversationMessagesView.as_view(),
        name="chat-conversation-messages",
    ),
    path("conversations/<int:pk>/read/", ConversationReadView.as_view(), name="chat-conversation-read"),
    path("attachments/<int:pk>/download/", AttachmentDownloadView.as_view(), name="chat-attachment-download"),
]
