import datetime
import json
from collections import defaultdict
from datetime import timedelta

from django.db.models import QuerySet
from django.http import HttpResponse, Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django_filters import FilterSet
from ics import Calendar
from ics.grammar.parse import ContentLine
from rest_framework import viewsets, permissions

from main.models import Bar, Weekday, Event
from main.serializers import BarSerializer, EventSerializer

from studibars.settings import TIME_ZONE


def exclude_symposion_events(events: QuerySet):
    now = datetime.datetime.now()
    # Check if it's a weekday (Monday=0, ..., Sunday=6) + if the time is between 6:00 and 19:00
    if 0 <= now.weekday() <= 4 and 6 <= now.hour < 19:
        return events.exclude(bar__name__icontains="symposion")
    return events


def should_display_events_menu_entry():
    events = Event.objects.filter(start_date__gte=datetime.date.today())
    events = exclude_symposion_events(events)
    return events.exists()


def main_view(request):
    json_ld = []
    bars_by_weekday = defaultdict(list)
    for bar in Bar.objects.all().order_by('start_time'):
        bars_by_weekday[bar.day].append(bar)
        json_ld.append(bar.to_json_ld())
    bars = []
    for day in Weekday.choices[:-3]:
        bars.append((day[1], bars_by_weekday[day[0]]))
    events = Event.objects.filter(start_date__gte=timezone.now() - timedelta(hours=8))
    for event in events:
        if not event.no_index:
            json_ld.append(event.to_json_ld())
    events = exclude_symposion_events(events)
    return render(request, 'main/main.html', {
        'title': 'Home',
        'display_events_menu_entry': should_display_events_menu_entry(),
        'json_ld': mark_safe(json.dumps(json_ld)),
        'weekdays': Weekday.choices[:-3],
        'bars_by_day': bars,
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'events': events.order_by('start_date'),
        'features': request.GET.get('features', '')
    })


def bar_view_name(request, name: str):
    name = name.replace('-', ' ')
    try:
        bar = Bar.objects.get(name__iexact=name)
    except Bar.DoesNotExist:
        raise Http404
    return bar_view_base(request, bar)


def bar_view_id(request, bar_id, name):
    try:
        bar = Bar.objects.get(id=bar_id)
    except Bar.DoesNotExist:
        raise Http404
    return bar_view_base(request, bar)


def bar_view_base(request, bar: Bar):
    json_ld = [bar.to_json_ld()]
    events = bar.event_set.filter(start_date__gte=timezone.now() - timedelta(hours=8))
    for event in events:
        if not event.no_index:
            json_ld.append(event.to_json_ld())
    events = exclude_symposion_events(events)
    return render(request, 'main/bar.html', {
        'canonical_url': bar.url_path(),
        'title': bar.name,
        'display_events_menu_entry': should_display_events_menu_entry(),
        'json_ld': mark_safe(json.dumps(json_ld)),
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'bar': bar,
        'events': events.order_by('start_date'),
        'content_description': bar.content_description(),
        'is_android': "Android" in request.META.get("HTTP_USER_AGENT", ""),
    })


def event_view(request, event_id, name, bar=""):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        raise Http404
    return render(request, 'main/event.html', {
        'canonical_url': event.url_path(),
        'title': f"{event.name} - {event.bar.name} - {event.start_date.date().strftime("%d.%m.%Y")}",
        'display_events_menu_entry': should_display_events_menu_entry(),
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'json_ld': mark_safe(json.dumps(event.to_json_ld())),
        'event': event,
        'content_description': event.content_description(),
        'no_index': event.no_index,
    })


def download_event_ics(request, name, event_id, bar):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return HttpResponse(status=404)

    c = Calendar()
    c.events.add(event.to_ics_event())

    response = HttpResponse(c.serialize(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename={event.name}.ics'
    return response


def download_bar_events_ics(request, bar_id, name=""):
    try:
        bar = Bar.objects.get(id=bar_id)
    except Event.DoesNotExist:
        return HttpResponse(status=404)

    c = Calendar()
    c.method = "PUBLISH"
    c.scale = "GREGORIAN"
    c.creator = "studibars-ac.de"
    # From https://stackoverflow.com/questions/17152251/specifying-name-description-and-refresh-interval-in-ical-ics-format#17187346
    c.extra.append(ContentLine(name="NAME", value=f"{bar.name} Events"))
    c.extra.append(ContentLine(name="X-WR-CALNAME", value=f"{bar.name} Events"))
    c.extra.append(ContentLine(name="TIMEZONE-ID", value=TIME_ZONE))
    c.extra.append(ContentLine(name="X-WR-TIMEZONE", value=TIME_ZONE))
    c.extra.append(ContentLine(name="URL", value=request.build_absolute_uri()))
    c.extra.append(ContentLine(name="REFRESH-INTERVAL", params={"VALUE": ["DURATION"]}, value="PT24H"))
    c.extra.append(ContentLine(name="X-PUBLISHED-TTL", value="PT24H"))

    for event in Event.objects.filter(bar_id=bar_id):
        c.events.add(event.to_ics_event())

    response = HttpResponse(c.serialize(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename={bar}-events.ics'
    return response


def robots(request):
    return render(request, 'main/robots.txt', {
        'sitemap': request.build_absolute_uri(reverse("sitemap")),
    })


def sitemap(request):
    sites = []
    now = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
    for event in Event.objects.filter(no_index=False):
        if event.start_date < now:
            prio = 0
        elif event.start_date < now + timedelta(days=10):
            prio = 1
        elif event.start_date < now + timedelta(days=21):
            prio = .8
        else:
            prio = .5
        sites.append((prio, request.build_absolute_uri(event.url_path()), event.updated_at))
    for bar in Bar.objects.all():
        sites.append((.5, request.build_absolute_uri(bar.url_path()), bar.updated_at))
    return render(request, 'main/sitemap.xml', {
        'sites': sites,
    }, content_type='application/xml; charset=utf-8')


# Allows all CRUP Operations
class BarFilter(FilterSet):
    class Meta:
        model = Bar
        fields = {
            'created_at': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'updated_at': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'name': ['iexact', 'icontains'],
            'description': ['icontains'],
            'day': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'tags': ['icontains'],
        }


class BarViewSet(viewsets.ModelViewSet):
    queryset = Bar.objects.all().filter()
    serializer_class = BarSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_class = BarFilter


class EventFilter(FilterSet):
    class Meta:
        model = Event
        fields = {
            'created_at': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'updated_at': ['exact', 'lt', 'lte', 'gt', 'gte'],
            'name': ['iexact', 'icontains'],
            'description': ['icontains'],
            'start_date': ['date', 'date__lt', 'date__lte', 'date__gte', 'date__gt', 'lt', 'lte', 'gt', 'gte'],
            'end_date': ['date', 'date__lt', 'date__lte', 'date__gte', 'date__gt', 'lt', 'lte', 'gt', 'gte'],
            'bar': ['exact'],
            'bar__name': ['iexact', 'icontains'],
        }


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().filter()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['name', 'description', 'bar', 'start_date', 'end_date']
    filterset_class = EventFilter
