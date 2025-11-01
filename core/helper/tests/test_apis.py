from django.test import TestCase
from core.tests.helper import SimpleCRUDMixinV2
from helper.models import AssignmentHelper


class TestUserAPI(TestCase, SimpleCRUDMixinV2):
    def setUp(self):
        super().setUp()
        self.model = AssignmentHelper
        self.url = 'assignment-helper'