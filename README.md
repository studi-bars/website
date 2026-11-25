# studi-bars

Dockerfile/compose von https://github.com/testdrivenio/django-on-docker/

# Local Development 

I recommend [PyCharm **Professional**](https://www.jetbrains.com/pycharm/download/) (Not the Community Edition. That edition can not auto complete django models etc.). The Professional Edition [is free for students](https://www.jetbrains.com/shop/eform/students).

1. Create a virtual environment: `python -m venv venv`
2. Activate the venv: `source venv/bin/activate` (done automatically in the PyCharm Terminal)
3. Install dependencies: `pip install -r requirements.txt`
4. Migrate Database: `python3 manage.py migrate`
5. Create initial Superuser: `python3 manage.py createsuperuser`
6. Run dev server: `python3 manage.py runserver`

# API Documentation

- REST API (OpenAPI): [`/api/docs/`](https://studibars-ac.de/api/docs/) (Swagger UI), [`/api/redoc/`](https://studibars-ac.de/api/redoc/), schema at `/api/schema.yaml`
- WebSocket API (AsyncAPI): [`/api/ws-docs/`](https://studibars-ac.de/api/ws-docs/), schema at `/api/asyncapi.yaml` / `/api/asyncapi.json`

The WebSocket endpoints `/api/events/subscribe` and `/api/bar/<bar_id>/events/subscribe` push a message whenever an event is created, updated or deleted.
The AsyncAPI schema is generated in [`main/asyncapi.py`](main/asyncapi.py) and reuses the `Event` schema of the REST API, so update the descriptions there when you change [`main/consumers.py`](main/consumers.py) or the signals in [`main/models.py`](main/models.py).
