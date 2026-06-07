from django.contrib import admin

from .models import Conversation, Message, MessageAttachment


class MessageAttachmentInline(admin.TabularInline):
    model = MessageAttachment
    extra = 0
    readonly_fields = ("original_name", "content_type", "size", "created_at")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("id", "conversation", "sender", "created_at", "read_at")
    list_filter = ("created_at", "read_at")
    search_fields = ("text", "sender__email", "sender__full_name")
    inlines = (MessageAttachmentInline,)


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "writer_profile", "updated_at")
    list_filter = ("created_at", "updated_at")
    search_fields = (
        "user__email",
        "user__full_name",
        "writer_profile__user__email",
        "writer_profile__user__full_name",
    )


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "message", "original_name", "content_type", "size", "created_at")
    search_fields = ("original_name", "message__text")
