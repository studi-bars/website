import datetime
import json
from collections import defaultdict
from datetime import timedelta

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

from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill

from studibars.settings import TIME_ZONE


class Thumbnail1x(ImageSpec):
    processors = [ResizeToFill(318, 180)]
    format = 'WEBP'


class Thumbnail1_5x(ImageSpec):
    processors = [ResizeToFill(int(318 * 1.5), int(180 * 1.5))]
    format = 'WEBP'


class Thumbnail2x(ImageSpec):
    processors = [ResizeToFill(318 * 2, 180 * 2)]
    format = 'WEBP'


register.generator('studibars:thumbnail1x', Thumbnail1x)
register.generator('studibars:thumbnail1_5x', Thumbnail1_5x)
register.generator('studibars:thumbnail2x', Thumbnail2x)


class Poster1x(ImageSpec):
    processors = [ResizeToFill(318, 450)]
    format = 'WEBP'


class Poster1_5x(ImageSpec):
    processors = [ResizeToFill(int(318 * 1.5), int(450 * 1.5))]
    format = 'WEBP'


class Poster2x(ImageSpec):
    processors = [ResizeToFill(318 * 2, 450 * 2)]
    format = 'WEBP'


register.generator('studibars:poster1x', Poster1x)
register.generator('studibars:poster1_5x', Poster1_5x)
register.generator('studibars:poster2x', Poster2x)


# Create your views here.
def main_view(request):
    json_ld = []
    bars_by_weekday = defaultdict(list)
    for bar in Bar.objects.all().order_by('start_time'):
        bars_by_weekday[bar.day].append(bar)
        json_ld.append(bar.to_json_ld())
    bars = []
    for day in Weekday.choices[:-3]:
        bars.append((day[1], bars_by_weekday[day[0]]))
    now = datetime.datetime.now()
    events = Event.objects.filter(start_date__gte=datetime.date.today())
    for event in events:
        json_ld.append(event.to_json_ld())
    # Check if it's a weekday (Monday=0, ..., Sunday=6) + if the time is between 6:00 and 19:00
    if 0 <= now.weekday() <= 4 and 6 <= now.hour < 19:
        events = events.exclude(bar__name__icontains="symposion")
    return render(request, 'main/main.html', {
        'title': 'Home',
        'json_ld': mark_safe(json.dumps(json_ld)),
        'weekdays': Weekday.choices[:-3],
        'bars_by_day': bars,
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'events': events.order_by('start_date'),
        'features': request.GET.get('features', '')
    })


def bar_view(request, bar_id, name):
    try:
        bar = Bar.objects.get(id=bar_id)
    except Bar.DoesNotExist:
        raise Http404
    json_ld = [bar.to_json_ld()]
    events = bar.event_set.filter(start_date__gte=datetime.date.today())
    for event in events:
        json_ld.append(event.to_json_ld())
    return render(request, 'main/bar.html', {
        'title': bar.name,
        'json_ld': mark_safe(json.dumps(json_ld)),
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'bar': bar,
        'events': events.order_by('start_date'),
    })


def event_view(request, event_id, name):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        raise Http404
    return render(request, 'main/event.html', {
        'title': f"{event.bar.name} - {event.name} - {event.start_date.date()}",
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'json_ld': mark_safe(json.dumps(event.to_json_ld())),
        'event': event,
    })


def download_event_ics(request, event_id):
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return HttpResponse(status=404)

    c = Calendar()
    c.events.add(event.to_ics_event())

    response = HttpResponse(c.serialize(), content_type='text/calendar')
    response['Content-Disposition'] = f'attachment; filename={event.name}.ics'
    return response


def download_bar_events_ics(request, bar_id):
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
    for event in Event.objects.all():
        if event.start_date < now:
            prio = 0
        elif event.start_date < now + timedelta(days=10):
            prio = 1
        elif event.start_date < now + timedelta(days=21):
            prio = .8
        else:
            prio = .5
        sites.append((prio, request.build_absolute_uri(event.url_path())))
    for bar in Bar.objects.all():
        sites.append((.5, request.build_absolute_uri(bar.url_path())))
    return render(request, 'main/sitemap.xml', {
        'sites': sites,
    }, content_type='application/xml; charset=utf-8')


# Allows all CRUP Operations
class BarFilter(FilterSet):
    class Meta:
        model = Bar
        fields = {
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
            'name': ['iexact', 'icontains'],
            'description': ['icontains'],
            'start_date': ['date', 'date__lte', 'date__gte', 'lt', 'lte', 'gt', 'gte'],
            'end_date': ['date', 'date__lte', 'date__gte', 'lt', 'lte', 'gt', 'gte'],
            'bar': ['exact'],
            'bar__name': ['iexact', 'icontains'],
        }


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all().filter()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['name', 'description', 'bar', 'start_date', 'end_date']
    filterset_class = EventFilter
