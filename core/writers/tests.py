from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase

from accounts.models import User
from writers.admin import ServiceAdmin, ServiceCategoryAdmin, SubjectAdmin
from writers.models import Education, Service, ServiceCategory, Subject


class WriterModelTests(TestCase):
    def test_education_subject_and_service_string_values(self):
        education = Education.objects.create(
            level=Education.Level.PHD,
            status=Education.Status.ONGOING,
        )
        subject = Subject.objects.create(name="Mathematics")
        category = ServiceCategory.objects.get(name="Writing & Research")
        service = Service.objects.create(name="Essay Writing", category=category)

        self.assertEqual(str(education), "PHD - Ongoing")
        self.assertEqual(str(subject), "Mathematics")
        self.assertEqual(str(category), "Writing & Research")
        self.assertEqual(str(service), "Essay Writing")


class WriterLookupAPITests(APITestCase):
    def test_service_list_is_public_read_only_lookup_data(self):
        writing = ServiceCategory.objects.get(name="Writing & Research")
        presentations = ServiceCategory.objects.get(name="Presentations")
        Service.objects.create(name="Report Writing", category=writing)
        Service.objects.create(name="Presentation Slides", category=presentations)

        response = self.client.get(reverse("writer-service-list"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual([service["name"] for service in response.data], ["Report Writing", "Presentation Slides"])
        self.assertEqual(response.data[0]["category_name"], "Writing & Research")
        self.assertEqual(response.data[0]["category_sort_order"], 1)

    def test_service_category_list_is_public_read_only_lookup_data(self):
        response = self.client.get(reverse("writer-service-category-list"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("Writing & Research", [category["name"] for category in response.data])
        self.assertIn("Business & Data", [category["name"] for category in response.data])


class AdminLookupPermissionTests(TestCase):
    def test_subject_and_service_admin_changes_require_admin_role_or_superuser(self):
        staff_user = User.objects.create_user(
            email="staff@example.com",
            password="password",
            is_staff=True,
        )
        admin_user = User.objects.create_user(
            email="admin@example.com",
            password="password",
            is_staff=True,
            role=User.Role.ADMIN,
        )
        superuser = User.objects.create_superuser(email="super@example.com", password="password")
        subject_admin = SubjectAdmin(Subject, None)
        service_admin = ServiceAdmin(Service, None)
        service_category_admin = ServiceCategoryAdmin(ServiceCategory, None)

        for model_admin in (subject_admin, service_admin, service_category_admin):
            request = type("Request", (), {"user": staff_user})
            self.assertFalse(model_admin.has_add_permission(request))
            self.assertFalse(model_admin.has_change_permission(request))
            self.assertFalse(model_admin.has_delete_permission(request))

            request = type("Request", (), {"user": admin_user})
            self.assertTrue(model_admin.has_add_permission(request))
            self.assertTrue(model_admin.has_change_permission(request))
            self.assertTrue(model_admin.has_delete_permission(request))

            request = type("Request", (), {"user": superuser})
            self.assertTrue(model_admin.has_add_permission(request))
            self.assertTrue(model_admin.has_change_permission(request))
            self.assertTrue(model_admin.has_delete_permission(request))
