from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import User
from writers.models import Education, WriterProfile

from .models import Conversation, Message, MessageAttachment


def make_upload(name="brief.pdf", content=b"%PDF-1.4 chat file", content_type="application/pdf"):
    return SimpleUploadedFile(name, content, content_type=content_type)


@override_settings(DEFAULT_FILE_STORAGE="django.core.files.storage.InMemoryStorage")
class ChatAPITests(APITestCase):
    def setUp(self):
        self.education = Education.objects.create(
            level=Education.Level.BACHELORS,
            status=Education.Status.COMPLETED,
        )
        self.user = User.objects.create_user(
            email="client@example.com",
            role=User.Role.USER,
            is_email_verified=True,
            is_profile_complete=True,
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            role=User.Role.USER,
            is_email_verified=True,
            is_profile_complete=True,
        )
        self.writer_user = User.objects.create_user(
            email="writer@example.com",
            role=User.Role.WRITER,
            is_email_verified=True,
            is_profile_complete=True,
        )
        self.writer_profile = WriterProfile.objects.create(
            user=self.writer_user,
            education=self.education,
            approval_status=WriterProfile.ApprovalStatus.APPROVED,
            approved_at=timezone.now(),
        )
        self.pending_writer_user = User.objects.create_user(
            email="pending@example.com",
            role=User.Role.WRITER,
            is_email_verified=True,
            is_profile_complete=True,
        )
        self.pending_writer = WriterProfile.objects.create(
            user=self.pending_writer_user,
            education=self.education,
            approval_status=WriterProfile.ApprovalStatus.PENDING,
        )
        self.admin = User.objects.create_superuser(email="admin@example.com", password="pass")

    def authenticate(self, user):
        self.client.force_authenticate(user=user)

    def create_conversation(self):
        return Conversation.objects.create(user=self.user, writer_profile=self.writer_profile)

    def test_user_can_create_conversation_with_approved_writer(self):
        self.authenticate(self.user)
        response = self.client.post(
            reverse("chat-conversation-list-create"),
            {"writer_profile_id": self.writer_profile.id},
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["writer_profile_id"], self.writer_profile.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_user_cannot_create_conversation_with_pending_writer(self):
        self.authenticate(self.user)
        response = self.client.post(
            reverse("chat-conversation-list-create"),
            {"writer_profile_id": self.pending_writer.id},
        )

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_writer_cannot_start_new_conversation(self):
        self.authenticate(self.writer_user)
        response = self.client.post(
            reverse("chat-conversation-list-create"),
            {"writer_profile_id": self.writer_profile.id},
        )

        self.assertEqual(response.status_code, 403)
        self.assertEqual(Conversation.objects.count(), 0)

    def test_duplicate_user_writer_pair_returns_existing_conversation(self):
        existing = self.create_conversation()
        self.authenticate(self.user)

        response = self.client.post(
            reverse("chat-conversation-list-create"),
            {"writer_profile_id": self.writer_profile.id},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], existing.id)
        self.assertEqual(Conversation.objects.count(), 1)

    def test_participants_and_admin_can_list_only_allowed_conversations(self):
        conversation = self.create_conversation()
        Conversation.objects.create(user=self.other_user, writer_profile=self.writer_profile)

        self.authenticate(self.user)
        user_response = self.client.get(reverse("chat-conversation-list-create"))
        self.assertEqual([item["id"] for item in user_response.data], [conversation.id])

        self.authenticate(self.writer_user)
        writer_response = self.client.get(reverse("chat-conversation-list-create"))
        self.assertEqual(len(writer_response.data), 2)

        self.authenticate(self.admin)
        admin_response = self.client.get(reverse("chat-conversation-list-create"))
        self.assertEqual(len(admin_response.data), 2)

    def test_message_requires_text_or_attachment(self):
        conversation = self.create_conversation()
        self.authenticate(self.user)

        response = self.client.post(
            reverse("chat-conversation-messages", args=[conversation.id]),
            {"text": ""},
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(Message.objects.count(), 0)

    def test_user_can_send_text_and_attachment_and_writer_can_read(self):
        conversation = self.create_conversation()
        self.authenticate(self.user)

        response = self.client.post(
            reverse("chat-conversation-messages", args=[conversation.id]),
            {
                "text": "Please review this brief.",
                "attachments": [make_upload()],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Message.objects.count(), 1)
        self.assertEqual(MessageAttachment.objects.count(), 1)
        message = Message.objects.get()
        self.assertEqual(message.sender, self.user)
        self.assertIsNotNone(message.delivered_at)

        self.authenticate(self.writer_user)
        read_response = self.client.post(reverse("chat-conversation-read", args=[conversation.id]))
        self.assertEqual(read_response.status_code, 200)
        message.refresh_from_db()
        self.assertIsNotNone(message.read_at)

    def test_attachment_validation_rejects_disallowed_too_large_and_too_many_files(self):
        conversation = self.create_conversation()
        self.authenticate(self.user)

        bad_type = self.client.post(
            reverse("chat-conversation-messages", args=[conversation.id]),
            {"attachments": [make_upload("archive.zip", b"zip", "application/zip")]},
            format="multipart",
        )
        self.assertEqual(bad_type.status_code, 400)

        too_large = self.client.post(
            reverse("chat-conversation-messages", args=[conversation.id]),
            {"attachments": [make_upload("large.pdf", b"x" * (10 * 1024 * 1024 + 1), "application/pdf")]},
            format="multipart",
        )
        self.assertEqual(too_large.status_code, 400)

        too_many = self.client.post(
            reverse("chat-conversation-messages", args=[conversation.id]),
            {"attachments": [make_upload(f"file-{index}.pdf") for index in range(6)]},
            format="multipart",
        )
        self.assertEqual(too_many.status_code, 400)
        self.assertEqual(MessageAttachment.objects.count(), 0)

    def test_private_attachment_download_rejects_non_participant(self):
        conversation = self.create_conversation()
        message = Message.objects.create(conversation=conversation, sender=self.user, text="File")
        attachment = MessageAttachment.objects.create(
            message=message,
            file=make_upload(),
            original_name="brief.pdf",
            content_type="application/pdf",
            size=20,
        )

        self.authenticate(self.other_user)
        blocked = self.client.get(reverse("chat-attachment-download", args=[attachment.id]))
        self.assertEqual(blocked.status_code, 404)

        self.authenticate(self.admin)
        allowed = self.client.get(reverse("chat-attachment-download", args=[attachment.id]))
        self.assertEqual(allowed.status_code, 200)
