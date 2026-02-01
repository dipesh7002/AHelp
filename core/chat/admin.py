from django.contrib import admin
from chat.models import Conversation, Room, Message 

admin.site.register(Conversation)
admin.site.register(Room)
admin.site.register(Message)