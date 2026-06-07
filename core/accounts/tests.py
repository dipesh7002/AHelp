from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase

from accounts.models import EmailOTP, User
from writers.models import Education, Service, Subject, WriterProfile, WriterWorkImage


def latest_otp_from_email():
    body = mail.outbox[-1].body
    return body.split("Your OTP is ")[1].split(".")[0]


def tiny_gif_upload(name):
    return SimpleUploadedFile(
        name,
        b"GIF87a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff,"
        b"\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;",
        content_type="image/gif",
    )


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class OTPAuthTests(APITestCase):
    def test_new_user_gets_complete_profile_next_step(self):
        self.client.post(reverse("user-request-otp"), {"email": "client@example.com"})
        response = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": latest_otp_from_email()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["next"], "complete_profile")
        self.assertIn("access", response.data["tokens"])

    def test_existing_complete_user_gets_dashboard_next_step(self):
        User.objects.create(
            email="client@example.com",
            full_name="Client One",
            role=User.Role.USER,
            is_email_verified=True,
            is_profile_complete=True,
        )

        self.client.post(reverse("user-request-otp"), {"email": "client@example.com"})
        response = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": latest_otp_from_email()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["next"], "dashboard")

    def test_user_profile_can_save_profile_picture(self):
        self.client.post(reverse("user-request-otp"), {"email": "client@example.com"})
        verify_response = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": latest_otp_from_email()},
        )
        token = verify_response.data["tokens"]["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.patch(
            reverse("user-profile"),
            {
                "full_name": "Client One",
                "profile_picture": tiny_gif_upload("client-profile.gif"),
                "location": "Kathmandu",
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        user = User.objects.get(email="client@example.com")
        self.assertTrue(user.profile_picture.name.startswith("users/profile-pictures/"))
        self.assertEqual(user.location, "Kathmandu")
        self.assertIn("users/profile-pictures/", response.data["user"]["profile_picture"])
        self.assertEqual(response.data["user"]["location"], "Kathmandu")

    def test_new_writer_gets_complete_writer_profile_next_step(self):
        self.client.post(reverse("writer-request-otp"), {"email": "writer@example.com"})
        response = self.client.post(
            reverse("writer-verify-otp"),
            {"email": "writer@example.com", "otp": latest_otp_from_email()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["next"], "complete_writer_profile")

    def test_writer_profile_completion_sets_pending_approval(self):
        education = Education.objects.create(
            level=Education.Level.BACHELORS,
            status=Education.Status.COMPLETED,
        )
        subject = Subject.objects.create(name="Computer Science")
        service = Service.objects.create(name="Report Writing")

        self.client.post(reverse("writer-request-otp"), {"email": "writer@example.com"})
        verify_response = self.client.post(
            reverse("writer-verify-otp"),
            {"email": "writer@example.com", "otp": latest_otp_from_email()},
        )
        token = verify_response.data["tokens"]["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.patch(
            reverse("writer-profile"),
            {
                "full_name": "Writer One",
                "profile_picture": tiny_gif_upload("writer-profile.gif"),
                "education": education.id,
                "subjects": [subject.id],
                "services": [service.id],
                "headline": "Academic Writer specializing in reports and presentations",
                "bio": "I help students and teams prepare clear academic work.",
                "languages": "English, Nepali",
                "location": "Nepal",
                "is_available": True,
                "cv": SimpleUploadedFile(
                    "writer-cv.pdf",
                    b"%PDF-1.4 test cv",
                    content_type="application/pdf",
                ),
                "work_images": [
                    tiny_gif_upload("work-1.gif"),
                    tiny_gif_upload("work-2.gif"),
                ],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["next"], "pending_approval")
        profile = WriterProfile.objects.get(user__email="writer@example.com")
        self.assertEqual(profile.approval_status, WriterProfile.ApprovalStatus.PENDING)
        self.assertTrue(profile.user.profile_picture.name.startswith("users/profile-pictures/"))
        self.assertIn("users/profile-pictures/", response.data["user"]["profile_picture"])
        self.assertEqual(mail.outbox[-1].to, ["assignmenthelperr0@gmail.com"])
        self.assertEqual(mail.outbox[-1].subject, "New writer application")
        self.assertIn("Writer One", mail.outbox[-1].body)
        self.assertIn("writer@example.com", mail.outbox[-1].body)
        self.assertIn("Academic Writer specializing in reports and presentations", mail.outbox[-1].body)
        self.assertIn("English, Nepali", mail.outbox[-1].body)
        self.assertIn("Nepal", mail.outbox[-1].body)
        self.assertIn("Computer Science", mail.outbox[-1].body)
        self.assertIn("Report Writing", mail.outbox[-1].body)
        self.assertEqual(len(mail.outbox[-1].attachments), 1)
        self.assertEqual(profile.headline, "Academic Writer specializing in reports and presentations")
        self.assertEqual(profile.bio, "I help students and teams prepare clear academic work.")
        self.assertEqual(profile.languages, "English, Nepali")
        self.assertEqual(profile.user.location, "Nepal")
        self.assertEqual(list(profile.services.values_list("name", flat=True)), ["Report Writing"])
        self.assertEqual(profile.work_images.count(), 2)
        self.assertEqual(
            list(profile.work_images.values_list("sort_order", flat=True)),
            [0, 1],
        )

    def test_writer_profile_rejects_more_than_eight_work_images(self):
        education = Education.objects.create(
            level=Education.Level.BACHELORS,
            status=Education.Status.COMPLETED,
        )

        self.client.post(reverse("writer-request-otp"), {"email": "writer@example.com"})
        verify_response = self.client.post(
            reverse("writer-verify-otp"),
            {"email": "writer@example.com", "otp": latest_otp_from_email()},
        )
        token = verify_response.data["tokens"]["access"]

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        response = self.client.patch(
            reverse("writer-profile"),
            {
                "full_name": "Writer One",
                "education": education.id,
                "cv": SimpleUploadedFile(
                    "writer-cv.pdf",
                    b"%PDF-1.4 test cv",
                    content_type="application/pdf",
                ),
                "work_images": [
                    tiny_gif_upload(f"work-{index}.gif")
                    for index in range(9)
                ],
            },
            format="multipart",
        )

        self.assertEqual(response.status_code, 400)
        self.assertEqual(WriterWorkImage.objects.count(), 0)

    def test_approved_writer_gets_writer_dashboard_next_step(self):
        education = Education.objects.create(
            level=Education.Level.MASTERS,
            status=Education.Status.COMPLETED,
        )
        user = User.objects.create(
            email="writer@example.com",
            full_name="Writer One",
            role=User.Role.WRITER,
            is_email_verified=True,
            is_profile_complete=True,
        )
        WriterProfile.objects.create(
            user=user,
            education=education,
            approval_status=WriterProfile.ApprovalStatus.APPROVED,
            approved_at=timezone.now(),
        )

        self.client.post(reverse("writer-request-otp"), {"email": "writer@example.com"})
        response = self.client.post(
            reverse("writer-verify-otp"),
            {"email": "writer@example.com", "otp": latest_otp_from_email()},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["next"], "writer_dashboard")

    def test_invalid_expired_reused_and_over_attempted_otps_are_rejected(self):
        self.client.post(reverse("user-request-otp"), {"email": "client@example.com"})
        otp = latest_otp_from_email()

        invalid = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": "000000"},
        )
        self.assertEqual(invalid.status_code, 400)

        valid = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": otp},
        )
        self.assertEqual(valid.status_code, 200)

        reused = self.client.post(
            reverse("user-verify-otp"),
            {"email": "client@example.com", "otp": otp},
        )
        self.assertEqual(reused.status_code, 400)

        self.client.post(reverse("user-request-otp"), {"email": "expired@example.com"})
        expired_otp = latest_otp_from_email()
        EmailOTP.objects.filter(email="expired@example.com").update(
            expires_at=timezone.now() - timezone.timedelta(minutes=1)
        )
        expired = self.client.post(
            reverse("user-verify-otp"),
            {"email": "expired@example.com", "otp": expired_otp},
        )
        self.assertEqual(expired.status_code, 400)

        self.client.post(reverse("user-request-otp"), {"email": "locked@example.com"})
        locked_otp = latest_otp_from_email()
        for _ in range(5):
            self.client.post(
                reverse("user-verify-otp"),
                {"email": "locked@example.com", "otp": "111111"},
            )
        locked = self.client.post(
            reverse("user-verify-otp"),
            {"email": "locked@example.com", "otp": locked_otp},
        )
        self.assertEqual(locked.status_code, 400)
