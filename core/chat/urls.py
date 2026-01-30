from rest_framework.routers import DefaultRouter
from chat.views import (
    RoomViewSet,
    MessageViewSet,
    ConversationViewSet
)

r = DefaultRouter()

r.register('room', RoomViewSet, 'room')
r.register('message', MessageViewSet, 'message')
r.register('conversation', ConversationViewSet, 'conversation')

urlpatterns = r.urls