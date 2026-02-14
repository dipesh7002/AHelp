from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from helper.models import Education, Subject


class HelperTests(APITestCase):
    def test_subject_string_representation(self):
        subject = Subject.objects.create(name="Math")
        self.assertEqual(str(subject), "Math")

    def test_assignment_helper_list_is_public(self):
        response = self.client.get(reverse("assignment-helper-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_education_list_is_public(self):
        Education.objects.create(
            level=Education.Level.BACHELORS,
            status=Education.Status.ONGOING,
        )
        response = self.client.get(reverse("education-list"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
