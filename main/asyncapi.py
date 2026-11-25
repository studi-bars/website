"""
AsyncAPI documentation for the WebSocket endpoints (see studibars/routing.py and main/consumers.py).

The payload schemas are taken from the drf-spectacular OpenAPI schema, so they always match
the REST API (/api/schema.yaml) and the data that is actually sent (EventSerializer).
"""
import copy
import json

import yaml
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from drf_spectacular.generators import SchemaGenerator

LOCAL_HOSTS = ('localhost', '127.0.0.1', '0.0.0.0')

DESCRIPTION = """Live notifications about created, updated and deleted events.

* The connection is **server → client only**. Messages sent by the client are ignored.
* No authentication is needed.
* There is no initial snapshot: fetch the current state from the REST API
  (`GET /api/events/`, see [/api/docs/](/api/docs/)) and apply the notifications on top of it.
* There is no replay: messages sent while a client is disconnected are lost.
  Reconnect (e.g. after a few seconds) and fetch the REST API again.
* WebSocket clients do **not** follow redirects. Use `studibars-ac.de`, the other domains
  (e.g. `studibars.de`) only redirect to it.

### Example

```js
function connect() {
    const ws = new WebSocket('wss://studibars-ac.de/api/bar/1/events/subscribe');
    ws.onmessage = (msg) => {
        const {event} = JSON.parse(msg.data);
        console.log(event.type, event.data.id, event.data.name);
    };
    ws.onclose = () => setTimeout(connect, 5000);
}
connect();
```
"""


def _openapi_to_json_schema(schema):
    """drf-spectacular emits OpenAPI 3.0 (`nullable: true`), AsyncAPI uses JSON Schema (`type: [..., 'null']`)."""
    if isinstance(schema, list):
        return [_openapi_to_json_schema(s) for s in schema]
    if not isinstance(schema, dict):
        return schema
    schema = {k: _openapi_to_json_schema(v) for k, v in schema.items()}
    if schema.pop('nullable', False):
        if 'type' in schema:
            schema['type'] = [schema['type'], 'null']
        elif '$ref' in schema:
            schema = {'oneOf': [{'$ref': schema.pop('$ref')}, {'type': 'null'}], **schema}
    return schema


def _notification_message(name, event_type, summary, description, example_data):
    return {
        'name': name,
        'title': f'Event {event_type}',
        'summary': summary,
        'description': description,
        'contentType': 'application/json',
        'payload': {
            'type': 'object',
            'required': ['type', 'event'],
            'properties': {
                'type': {
                    'type': 'string',
                    'const': 'event_notification',
                    'description': 'Internal channel-layer message type, always `event_notification`.',
                },
                'event': {
                    'type': 'object',
                    'required': ['type', 'data'],
                    'properties': {
                        'type': {'type': 'string', 'const': event_type},
                        'data': {'$ref': '#/components/schemas/Event'},
                    },
                },
            },
        },
        'examples': [{
            'name': name,
            'payload': {'type': 'event_notification', 'event': {'type': event_type, 'data': example_data}},
        }],
    }


def build_asyncapi_schema(request):
    openapi_components = SchemaGenerator().get_schema(request=None, public=True)['components']['schemas']
    schemas = {name: _openapi_to_json_schema(copy.deepcopy(openapi_components[name]))
               for name in ('Event', 'SpecialDrink')}

    example_event = {
        'id': 42,
        'special_drinks': [{
            'id': 7, 'name': 'Mexikaner', 'price': 1, 'quantity': 2,
            'ingredients': 'Tomatensaft, Korn, Tabasco', 'note': 'ab 22 Uhr', 'event': 42,
        }],
        'created_at': '2026-11-20T18:03:12.123456+01:00',
        'updated_at': '2026-11-20T18:03:12.123456+01:00',
        'name': 'Glühweinparty',
        'description': 'Glühwein für alle!',
        'emoji': '🍷',
        'start_date': '2026-12-03T21:00:00+01:00',
        'end_date': None,
        'poster': None,
        'no_index': False,
        'recurring': False,
        'bar': 1,
    }

    host = request.get_host()
    is_local = host.startswith(LOCAL_HOSTS)
    # Behind nginx Django does not know about TLS, so derive the scheme from the host
    rest_docs_url = f"{'http' if is_local else 'https'}://{host}{reverse('swagger-ui')}"
    servers = {}
    if not is_local:
        servers['production'] = {'host': host, 'protocol': 'wss', 'description': 'This server'}
    servers['local'] = {'host': 'localhost:8000', 'protocol': 'ws',
                        'description': 'Local development server (`python manage.py runserver`)'}

    message_refs = {
        'eventCreated': {'$ref': '#/components/messages/eventCreated'},
        'eventUpdated': {'$ref': '#/components/messages/eventUpdated'},
        'eventDeleted': {'$ref': '#/components/messages/eventDeleted'},
    }

    return {
        'asyncapi': '3.0.0',
        'info': {
            'title': 'Studibars WebSocket API',
            'version': '1.0.0',
            'description': DESCRIPTION,
            'externalDocs': {'description': 'REST API (OpenAPI)', 'url': rest_docs_url},
        },
        'defaultContentType': 'application/json',
        'servers': servers,
        'channels': {
            'allEvents': {
                'address': '/api/events/subscribe',
                'title': 'All events',
                'description': 'Notifications for events of **all** bars.',
                'messages': message_refs,
            },
            'barEvents': {
                'address': '/api/bar/{bar_id}/events/subscribe',
                'title': 'Events of one bar',
                'description': 'Notifications only for events whose `bar` equals `bar_id`. '
                               'A `bar_id` of `0` behaves like `/api/events/subscribe`.',
                'parameters': {
                    'bar_id': {
                        'description': 'ID of the bar (`id` from `GET /api/bars/`). Must be numeric, '
                                       'otherwise the connection is rejected.',
                        'examples': ['1'],
                    },
                },
                'messages': message_refs,
            },
        },
        'operations': {
            'sendAllEvents': {
                'action': 'send',
                'channel': {'$ref': '#/channels/allEvents'},
                'title': 'Event notifications (all bars)',
                'messages': [{'$ref': f'#/channels/allEvents/messages/{m}'} for m in message_refs],
            },
            'sendBarEvents': {
                'action': 'send',
                'channel': {'$ref': '#/channels/barEvents'},
                'title': 'Event notifications (one bar)',
                'messages': [{'$ref': f'#/channels/barEvents/messages/{m}'} for m in message_refs],
            },
        },
        'components': {
            'schemas': schemas,
            'messages': {
                'eventCreated': _notification_message(
                    'eventCreated', 'created', 'An event was created.',
                    'Sent after a new event was saved (e.g. in the admin), including its special drinks.',
                    example_event),
                'eventUpdated': _notification_message(
                    'eventUpdated', 'updated', 'An event was changed.',
                    'Sent every time an existing event is saved, even if nothing changed '
                    '(saving in the admin always triggers it). Changing the special drinks in the admin '
                    'also saves the event, so `special_drinks` is always up-to-date.',
                    example_event),
                'eventDeleted': _notification_message(
                    'eventDeleted', 'deleted', 'An event was deleted.',
                    '`data` contains the event (including its special drinks) as it was before the deletion.',
                    example_event),
            },
        },
    }


class _YamlDumper(yaml.SafeDumper):
    pass


def _represent_str(dumper, value):
    # Use the readable `|` block style for multiline strings (descriptions)
    return dumper.represent_scalar('tag:yaml.org,2002:str', value, style='|' if '\n' in value else None)


_YamlDumper.add_representer(str, _represent_str)


def asyncapi_schema_view(request):
    schema = build_asyncapi_schema(request)
    if request.path.endswith('.json'):
        return HttpResponse(json.dumps(schema, indent=2, ensure_ascii=False), content_type='application/json')
    return HttpResponse(yaml.dump(schema, Dumper=_YamlDumper, sort_keys=False, allow_unicode=True, width=120),
                        content_type='application/yaml')


def asyncapi_docs_view(request):
    return render(request, 'main/asyncapi.html', {'schema_url': reverse('asyncapi-schema-json')})
