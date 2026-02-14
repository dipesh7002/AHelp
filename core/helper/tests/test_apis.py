from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AssignmentHelperApiTests(APITestCase):
    def test_assignment_helper_create_requires_authentication(self):
        response = self.client.post(reverse("assignment-helper-list"), {}, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
