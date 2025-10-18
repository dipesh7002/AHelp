from django.urls import path, include
from rest_framework.routers import DefaultRouter

from authentication.views import CommonUserViewset

r = DefaultRouter()

r.register('user', CommonUserViewset, basename='user')

urlpatterns = r.urls