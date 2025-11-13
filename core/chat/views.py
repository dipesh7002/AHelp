from rest_framework.viewsets import ModelViewSet
from chat.models import(
    Room, 
    Message
)
from chat.serializers import(
    RoomSerializer,
    MessageSerializer
)

class RoomViewSet(ModelViewSet):
    queryset = Room.objects.all()
    serializer_class = RoomSerializer
    
class MessageViewSet(ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    
