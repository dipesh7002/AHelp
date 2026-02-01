from django.urls import path
from . import views

urlpatterns = [
    # Instagram settings endpoints
    path('instagram/', views.instagram_settings, name='instagram-settings'),
    path('test/instagram/', views.test_instagram_connection, name='test-instagram'),
]
