from django.urls import re_path
from main.consumers import EventConsumer

websocket_urlpatterns = [
    re_path(r'api/events/subscribe$', EventConsumer.as_asgi()),
    re_path(r'api/bars/(?P<bar_id>\d+)/events/subscribe$', EventConsumer.as_asgi()),
]
