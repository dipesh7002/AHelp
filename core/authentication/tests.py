from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CommonUser


class AuthenticationTests(APITestCase):
    def test_admin_role_sets_staff_and_superuser_flags(self):
        user = CommonUser.objects.create(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=CommonUser.Role.ADMIN,
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_verify_email_requires_payload(self):
        response = self.client.post(reverse("verify_email"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
