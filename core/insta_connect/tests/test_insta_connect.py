from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CommonUser
from insta_connect.models import InstagramAccount


class InstaConnectTests(APITestCase):
    def test_instagram_callback_without_code_requires_authentication(self):
        response = self.client.get(reverse("instagram-callback"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_instagram_account_string_representation(self):
        user = CommonUser.objects.create(
            email="insta@example.com",
            first_name="Insta",
            last_name="User",
            role=CommonUser.Role.COMMON,
        )
        account = InstagramAccount.objects.create(
            user=user,
            instagram_business_account_id="biz-1",
            instagram_username="insta_user",
            access_token="token",
            facebook_page_id="page-1",
            facebook_page_name="Page Name",
        )
        self.assertIn("@insta_user", str(account))
