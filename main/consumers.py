import json
from channels.generic.websocket import AsyncWebsocketConsumer

CHANNEL_GROUP_NAME = 'events'


class EventConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.bar_id = int(self.scope['url_route']['kwargs'].get('bar_id', 0))
        await self.channel_layer.group_add(CHANNEL_GROUP_NAME, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(CHANNEL_GROUP_NAME, self.channel_name)

    async def event_notification(self, event):
        if not self.bar_id or self.bar_id == event['event']['data']['bar']:
            await self.send(text_data=json.dumps(event))
