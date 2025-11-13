from rest_framework.routers import DefaultRouter
from chat.views import (
    RoomViewSet,
    MessageViewSet
)

r = DefaultRouter()

r.register('room', RoomViewSet, 'room')
r.register('message', MessageViewSet, 'message')

urlpatterns = r.urls