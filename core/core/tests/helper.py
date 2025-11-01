from django.urls import reverse
from rest_framework import status
from core.tests.prepare import create_super_user

from model_bakery import baker
import random


class SimpleCRUDMixinV2:

    url_list: str
    url_detail: str

    def _bake_properly(self, **kwargs):
        initial_data = baker.prepare(self.model, **kwargs).__dict__
        filtered_data = self._clean_initial_data(initial_data)
        return filtered_data

    def _clean_initial_data(self, initial_data):
        initial_data.pop("_state")
        filtered_data = {}
        for key, value in initial_data.items():
            if value is not None and value != "":
                filtered_data[key] = value
        return filtered_data

    def _create(self):
        self.url_list = reverse(f"{self.url}-list")
        filtered_data = self._bake_properly()
        response = self.client.post(self.url_list, filtered_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        return response.data["id"]

    def create_and_authenticate_user(
        self, email="valid@user.mail", password="validpassword"
    ):
        user = create_super_user(email=email, password=password)
        user.save()
        self.client.force_authenticate(user=user)
        return user

    def _patch_value_generator(self):
        initial_data = baker.prepare(self.model).__dict__
        filtered_data = self._clean_initial_data(initial_data)
        filtered_data_len = len(filtered_data)
        chosen = random.randint(0, (filtered_data_len - 1))
        diff = filtered_data_len - chosen
        while diff:
            filtered_data.popitem()
            diff -= 1
        return filtered_data

    def test_create_list(self):
        self.create_and_authenticate_user(self.client)
        self.url_list = reverse(f"{self.url}-list")
        baker.make(self.model, _quantity=2)
        response = self.client.get(self.url_list)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)
        self._create()

    def test_retrieve_update_delete(self):
        self.create_and_authenticate_user(self.client)
        self.url_detail = reverse(f"{self.url}-detail", args=[self._create()])

        # retrieve
        response_retrieve = self.client.get(self.url_detail)
        self.assertEqual(response_retrieve.status_code, status.HTTP_200_OK)

        # put
        updated_data = self._bake_properly()
        response_put = self.client.put(self.url_detail, updated_data, format="json")
        self.assertEqual(response_put.status_code, status.HTTP_200_OK)

        # patch
        updated_data = self._patch_value_generator()
        response_patch = self.client.patch(self.url_detail, updated_data, format="json")
        self.assertEqual(response_patch.status_code, status.HTTP_200_OK)

        # deletion
        response_delete = self.client.delete(self.url_detail)
        self.assertEqual(response_delete.status_code, status.HTTP_204_NO_CONTENT)
