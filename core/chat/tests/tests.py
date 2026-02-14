from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from authentication.models import CommonUser
from chat.models import Conversation


class ChatTests(APITestCase):
    def setUp(self):
        self.user_1 = CommonUser.objects.create(
            email="u1@example.com",
            first_name="User",
            last_name="One",
            role=CommonUser.Role.COMMON,
        )
        self.user_2 = CommonUser.objects.create(
            email="u2@example.com",
            first_name="User",
            last_name="Two",
            role=CommonUser.Role.HELPER,
        )

    def test_conversation_has_participant(self):
        conversation = Conversation.objects.create(
            participant1=self.user_1,
            participant2=self.user_2,
        )
        self.assertTrue(conversation.has_participant(self.user_1))
        self.assertEqual(conversation.get_other_participant(self.user_1), self.user_2)

    def test_conversation_list_requires_authentication(self):
        response = self.client.get(reverse("conversation-list"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
