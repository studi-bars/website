import json
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Event
from .serializers import EventSerializer

CHANNEL_GROUP_NAME = 'events'


class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bar_id = self.scope['url_route']['kwargs'].get('bar_id')
        await self.channel_layer.group_add(CHANNEL_GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(CHANNEL_GROUP_NAME, self.channel_name)

    async def event_notification(self, event):
        if not self.bar_id or self.bar_id == event['event']['data']['id']:
            await self.send(text_data=json.dumps(event))


@receiver(post_save, sender=Event)
def event_saved(sender, instance, created, **kwargs):
    channel_layer = get_channel_layer()
    event_type = 'created' if created else 'updated'
    data = EventSerializer(instance).data
    async_to_sync(channel_layer.group_send)(
        CHANNEL_GROUP_NAME,
        {
            'type': 'event_notification',
            'event': {
                'type': event_type,
                'data': data
            }
        }
    )


@receiver(post_delete, sender=Event)
def event_deleted(sender, instance, **kwargs):
    channel_layer = get_channel_layer()
    data = EventSerializer(instance).data
    async_to_sync(channel_layer.group_send)(
        CHANNEL_GROUP_NAME,
        {
            'type': 'event_notification',
            'event': {
                'type': 'deleted',
                'data': data
            }
        }
    )
