import datetime
from collections import defaultdict

from django.http import HttpResponse, Http404
from django.shortcuts import render
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
    bars_by_weekday = defaultdict(list)
    for bar in Bar.objects.all().order_by('start_time'):
        bars_by_weekday[bar.day].append(bar)
    bars = []
    for day in Weekday.choices[:-3]:
        bars.append((day[1], bars_by_weekday[day[0]]))
    now = datetime.datetime.now()
    events = Event.objects.filter(start_date__gte=datetime.date.today())
    # Check if it's a weekday (Monday=0, ..., Sunday=6) + if the time is between 6:00 and 19:00
    if 0 <= now.weekday() <= 4 and 6 <= now.hour < 19:
        events = events.exclude(bar__name__icontains="symposion")
    return render(request, 'main/main.html', {
        'title': 'Home',
        'weekdays': Weekday.choices[:-3],
        'bars_by_day': bars,
        'bars': Bar.objects.all().order_by('day', 'start_time'),
        'events': events.order_by('start_date'),
        'features': request.GET.get('features', '')
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


# Allows all CRUP Operations
class BarViewSet(viewsets.ModelViewSet):
    queryset = Bar.objects.all()
    serializer_class = BarSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['name', 'description', 'day', 'start_time', 'end_time', 'open', 'tags']


class EventViewSet(viewsets.ModelViewSet):
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filterset_fields = ['name', 'description', 'bar', 'start_date', 'end_date']
