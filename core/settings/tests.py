from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Setting, InstagramSettings, EmailSettings

User = get_user_model()


class SettingModelTest(TestCase):
    def test_setting_creation(self):
        setting = Setting.objects.create(
            key='test_key',
            value='test_value',
            category='test'
        )
        self.assertEqual(setting.key, 'test_key')
        self.assertEqual(setting.value, 'test_value')

    def test_typed_value_boolean(self):
        setting = Setting.objects.create(
            key='bool_setting',
            value='true',
            setting_type='boolean'
        )
        self.assertTrue(setting.get_typed_value())

        setting.value = 'false'
        setting.save()
        self.assertFalse(setting.get_typed_value())

    def test_typed_value_number(self):
        setting = Setting.objects.create(
            key='num_setting',
            value='42',
            setting_type='number'
        )
        self.assertEqual(setting.get_typed_value(), 42)

    def test_get_value_classmethod(self):
        Setting.objects.create(key='test_key', value='test_value')
        self.assertEqual(Setting.get_value('test_key'), 'test_value')
        self.assertEqual(Setting.get_value('nonexistent', 'default'), 'default')


class SettingsAPITest(APITestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpass',
            role='admin'
        )
        self.client.force_authenticate(user=self.admin_user)

    def test_instagram_settings_get(self):
        response = self.client.get('/api/settings/instagram/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('app_id', response.data)

    def test_instagram_settings_update(self):
        data = {
            'app_id': '123456789',
            'app_secret': 'test_secret',
            'api_version': 'v20.0'
        }
        response = self.client.put('/api/settings/instagram/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['app_id'], '123456789')

    def test_email_settings_get(self):
        response = self.client.get('/api/settings/email/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('host', response.data)

    def test_email_settings_update(self):
        data = {
            'host': 'smtp.example.com',
            'port': 587,
            'username': 'test@example.com'
        }
        response = self.client.put('/api/settings/email/', data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['host'], 'smtp.example.com')

    def test_settings_overview(self):
        response = self.client.get('/api/settings/overview/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('instagram', response.data)
        self.assertIn('email', response.data)
        self.assertIn('google', response.data)
        self.assertIn('system', response.data)

    def test_generic_settings_crud(self):
        # Create
        data = {
            'key': 'test_setting',
            'value': 'test_value',
            'category': 'test',
            'description': 'Test setting'
        }
        response = self.client.post('/api/settings/settings/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        setting_id = response.data['id']

        # Read
        response = self.client.get(f'/api/settings/settings/{setting_id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['key'], 'test_setting')

        # Update
        update_data = {'value': 'updated_value'}
        response = self.client.patch(f'/api/settings/settings/{setting_id}/', update_data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['value'], 'updated_value')

        # Delete
        response = self.client.delete(f'/api/settings/settings/{setting_id}/')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
