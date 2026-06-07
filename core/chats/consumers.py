from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from django.contrib.auth import get_user_model
from django.utils import timezone

from .events import user_group_name
from .presence import mark_offline, mark_online

User = get_user_model()


@database_sync_to_async
def touch_last_seen(user_id):
    User.objects.filter(pk=user_id).update(last_seen_at=timezone.now())


class ChatConsumer(AsyncJsonWebsocketConsumer):
    async def connect(self):
        user = self.scope.get("user")
        if not user or not user.is_authenticated:
            await self.close(code=4401)
            return

        self.user_id = user.id
        self.group_name = user_group_name(user.id)
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        mark_online(user.id)
        await touch_last_seen(user.id)
        await self.accept()
        await self.send_json({"event": "connected", "payload": {"user_id": user.id}})

    async def disconnect(self, close_code):
        if hasattr(self, "user_id"):
            mark_offline(self.user_id)
            await touch_last_seen(self.user_id)
        if hasattr(self, "group_name"):
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive_json(self, content, **kwargs):
        if content.get("event") == "ping":
            if hasattr(self, "user_id"):
                mark_online(self.user_id)
            await self.send_json({"event": "pong", "payload": {}})

    async def chat_event(self, event):
        await self.send_json(
            {
                "event": event["event"],
                "payload": event["payload"],
            }
        )
