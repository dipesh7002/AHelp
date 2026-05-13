from django.test import TestCase

from writers.models import Education, Subject


class WriterModelTests(TestCase):
    def test_education_and_subject_string_values(self):
        education = Education.objects.create(
            level=Education.Level.PHD,
            status=Education.Status.ONGOING,
        )
        subject = Subject.objects.create(name="Mathematics")

        self.assertEqual(str(education), "PHD - Ongoing")
        self.assertEqual(str(subject), "Mathematics")
