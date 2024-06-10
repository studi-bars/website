from collections import defaultdict
from django.shortcuts import render
from rest_framework import viewsets, permissions

from main.models import Bar, Weekday, Event
from main.serializers import BarSerializer, EventSerializer

from imagekit import ImageSpec, register
from imagekit.processors import ResizeToFill


class Thumbnail(ImageSpec):
    processors = [ResizeToFill(318 * 2, 180 * 2)]
    format = 'WEBP'


register.generator('studibars:thumbnail', Thumbnail)


# Create your views here.
def main_view(request):
    bars_by_weekday = defaultdict(list)
    for bar in Bar.objects.all():
        bars_by_weekday[bar.day].append(bar)
    bars = []
    for day in Weekday.choices[:-3]:
        bars.append((day[1], bars_by_weekday[day[0]]))
    return render(request, 'main/main.html', {
        'title': 'Home',
        'weekdays': Weekday.choices[:-3],
        'bars_by_day': bars,
        'bars': Bar.objects.all().order_by('day'),
        'events': Event.objects.all().order_by('start_date'),
        'features': request.GET.get('features', '')
    })


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
