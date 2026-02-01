from djangochannelsrestframework.mixins import CreateModelMixin
from channels.db import database_sync_to_async
from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin, action

from chat.models import Message
from chat.serializers import MessageSerializer


class RoomConsumer(CreateModelMixin, ObserverModelInstanceMixin, GenericAsyncAPIConsumer):

    @model_observer(Message)
    async def message_activity(
        self,
        message,
        observer=None,
        subscribing_request_ids=[],
        **kwargs
    ):
        for request_id in subscribing_request_ids:
            message_body = dict(request_id=request_id)
            message_body.update(message)
            await self.send_json(message_body)

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f'room__{instance.conversation_id}'

    @message_activity.groups_for_consumer
    def message_activity(self, room=None, **kwargs):
        if room is not None:
            yield f'room__{room}'

    @message_activity.serializer
    def message_activity(self, instance: Message, action, **kwargs):
        return dict(
            data=MessageSerializer(instance).data,
            action=action.value,
            pk=instance.pk
        )
        
    async def join_room(self, pk, request_id, **kwargs):
        room = await database_sync_to_async(self.get_object)(pk=pk)
        await self.subscribe_instance(request_id=request_id, pk=room.pk)
        await self.message_activity.subscribe(room=pk, request_id=request_id)
        await self.add_user_to_room(room)

    @action()
    async def leave_room(self, pk, **kwargs):
        room = await database_sync_to_async(self.get_object)(pk=pk)
        await self.unsubscribe_instance(pk=room.pk)
        await self.message_activity.unsubscribe(room=room.pk)
        await self.remove_user_from_room(room)