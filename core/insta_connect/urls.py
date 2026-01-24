from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views, webhooks

# Create router for viewsets
router = DefaultRouter()
router.register(r'accounts', views.InstagramAccountViewSet, basename='instagram-account')
router.register(r'conversations', views.InstagramConversationViewSet, basename='instagram-conversation')

urlpatterns = [
    # OAuth Flow
    path('connect/', views.instagram_connect, name='instagram-connect'),
    path('callback/', views.instagram_callback, name='instagram-callback'),
    path('complete/', views.instagram_complete_connection, name='instagram-complete'),
    
    # Webhook
    path('webhook/', webhooks.instagram_webhook, name='instagram-webhook'),
    
    # Messaging
    path('send-message/', views.send_message, name='instagram-send-message'),
    path('send-media/', views.send_media_message, name='instagram-send-media'),
    
    # ViewSets
    path('', include(router.urls)),
]
