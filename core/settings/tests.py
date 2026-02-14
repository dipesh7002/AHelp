from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CommonUser
from settings.models import InstagramSettings


class InstagramSettingsModelTests(APITestCase):
    def test_graph_api_url_uses_api_version(self):
        settings_obj = InstagramSettings.objects.create(api_version="v22.0")
        self.assertEqual(settings_obj.graph_api_url, "https://graph.facebook.com/v22.0")


class SettingsApiTests(APITestCase):
    def setUp(self):
        self.admin_user = CommonUser.objects.create(
            email="admin@example.com",
            first_name="Admin",
            last_name="User",
            role=CommonUser.Role.ADMIN,
        )

    def test_instagram_settings_requires_authentication(self):
        response = self.client.get(reverse("instagram-settings"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_instagram_settings_get_for_admin(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.get(reverse("instagram-settings"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("api_version", response.data)

    def test_test_instagram_connection_returns_400_if_not_configured(self):
        self.client.force_authenticate(self.admin_user)
        response = self.client.post(reverse("test-instagram"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
