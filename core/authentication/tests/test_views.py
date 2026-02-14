from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CommonUser


class CommonUserViewsetTests(APITestCase):
    def setUp(self):
        self.user = CommonUser.objects.create(
            email="member@example.com",
            first_name="Member",
            last_name="User",
            role=CommonUser.Role.COMMON,
        )

    def test_user_list_requires_authentication(self):
        response = self.client.get(reverse("user-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_change_password_requires_old_and_new_password(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(reverse("user-change-password"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
