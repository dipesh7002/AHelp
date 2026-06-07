from pathlib import Path

from django.contrib.auth import get_user_model
from django.db import transaction
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from writers.models import WriterProfile

from .events import broadcast_conversation_event
from .models import Conversation, Message, MessageAttachment
from .serializers import (
    ConversationSerializer,
    MAX_ATTACHMENTS_PER_MESSAGE,
    MessageSerializer,
    validate_chat_attachment,
)

User = get_user_model()


def is_admin_user(user):
    return user.is_staff or user.is_superuser or user.role == User.Role.ADMIN


def conversation_queryset():
    return (
        Conversation.objects
        .select_related("user", "writer_profile", "writer_profile__user")
        .prefetch_related("messages", "messages__attachments", "messages__sender")
    )


def conversations_for_user(user):
    queryset = conversation_queryset()
    if is_admin_user(user):
        return queryset
    if user.role == User.Role.WRITER:
        return queryset.filter(writer_profile__user=user)
    return queryset.filter(user=user)


def get_accessible_conversation(user, pk):
    try:
        return conversations_for_user(user).get(pk=pk)
    except Conversation.DoesNotExist as exc:
        raise Http404 from exc


def serialize_message(request, message):
    return MessageSerializer(message, context={"request": request}).data


def serialize_conversation(request, conversation):
    return ConversationSerializer(conversation, context={"request": request}).data


class ConversationListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = ConversationSerializer(
            conversations_for_user(request.user),
            many=True,
            context={"request": request},
        )
        return Response(serializer.data)

    def post(self, request):
        if request.user.role != User.Role.USER:
            return Response(
                {"detail": "Only users can start a conversation with a writer."},
                status=status.HTTP_403_FORBIDDEN,
            )

        writer_profile_id = request.data.get("writer_profile_id")
        writer = get_object_or_404(
            WriterProfile.objects.select_related("user"),
            pk=writer_profile_id,
            approval_status=WriterProfile.ApprovalStatus.APPROVED,
        )
        if writer.user_id == request.user.id:
            return Response(
                {"detail": "You cannot start a conversation with yourself."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        conversation, created = Conversation.objects.get_or_create(
            user=request.user,
            writer_profile=writer,
        )
        serializer = ConversationSerializer(conversation, context={"request": request})
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class ConversationMessagesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [JSONParser, MultiPartParser, FormParser]

    def get(self, request, pk):
        conversation = get_accessible_conversation(request.user, pk)
        messages = (
            conversation.messages
            .select_related("sender")
            .prefetch_related("attachments")
            .all()
        )
        serializer = MessageSerializer(messages, many=True, context={"request": request})
        return Response(serializer.data)

    @transaction.atomic
    def post(self, request, pk):
        conversation = get_accessible_conversation(request.user, pk)
        if is_admin_user(request.user):
            return Response(
                {"detail": "Admins can view conversations but cannot send participant messages."},
                status=status.HTTP_403_FORBIDDEN,
            )
        if request.user.id not in {conversation.user_id, conversation.writer_profile.user_id}:
            raise Http404

        text = (request.data.get("text") or "").strip()
        attachments = request.FILES.getlist("attachments")

        if len(attachments) > MAX_ATTACHMENTS_PER_MESSAGE:
            return Response(
                {"attachments": f"Send at most {MAX_ATTACHMENTS_PER_MESSAGE} files per message."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not text and not attachments:
            return Response(
                {"detail": "Message text or at least one attachment is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        for attachment in attachments:
            try:
                validate_chat_attachment(attachment)
            except Exception as exc:
                return Response({"attachments": [str(exc)]}, status=status.HTTP_400_BAD_REQUEST)

        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            text=text,
            delivered_at=timezone.now(),
        )
        for uploaded_file in attachments:
            MessageAttachment.objects.create(
                message=message,
                file=uploaded_file,
                original_name=Path(uploaded_file.name).name,
                content_type=getattr(uploaded_file, "content_type", "") or "application/octet-stream",
                size=uploaded_file.size,
            )
        conversation.save(update_fields=["updated_at"])

        message = (
            Message.objects
            .select_related("sender")
            .prefetch_related("attachments")
            .get(pk=message.pk)
        )
        payload = {
            "conversation": serialize_conversation(request, conversation),
            "message": serialize_message(request, message),
        }
        broadcast_conversation_event(conversation, "new_message", payload)
        broadcast_conversation_event(conversation, "conversation_updated", payload)
        return Response(payload["message"], status=status.HTTP_201_CREATED)


class ConversationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        conversation = get_accessible_conversation(request.user, pk)
        if is_admin_user(request.user):
            return Response(
                {"detail": "Admins do not change participant read state."},
                status=status.HTTP_403_FORBIDDEN,
            )

        now = timezone.now()
        updated = (
            conversation.messages
            .filter(read_at__isnull=True)
            .exclude(sender=request.user)
            .update(read_at=now)
        )
        payload = {
            "conversation_id": conversation.id,
            "reader_id": request.user.id,
            "read_at": now.isoformat(),
            "updated_count": updated,
        }
        broadcast_conversation_event(conversation, "message_read", payload)
        broadcast_conversation_event(
            conversation,
            "conversation_updated",
            {"conversation": serialize_conversation(request, conversation)},
        )
        return Response(payload)


class AttachmentDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        attachment = get_object_or_404(
            MessageAttachment.objects.select_related(
                "message",
                "message__conversation",
                "message__conversation__user",
                "message__conversation__writer_profile",
                "message__conversation__writer_profile__user",
            ),
            pk=pk,
        )
        conversation = attachment.message.conversation
        if (
            not is_admin_user(request.user)
            and request.user.id not in {conversation.user_id, conversation.writer_profile.user_id}
        ):
            raise Http404
        attachment.file.open("rb")
        return FileResponse(
            attachment.file,
            as_attachment=True,
            filename=attachment.original_name,
            content_type=attachment.content_type,
        )
