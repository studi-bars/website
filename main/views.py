from collections import defaultdict
from email._header_value_parser import BareQuotedString

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from main.models import WeekdayField, Bar


# Create your views here.
def main_view(request):
    bars_by_weekday = defaultdict(list)
    for bar in Bar.objects.all():
        bars_by_weekday[bar.day].append(bar)
    bars = []
    for day in WeekdayField.WEEKDAY_CHOICES[:-3]:
        bars.append((day[1], bars_by_weekday[day[0]]))
    return render(request, 'main/main.html', {
        'title': 'Home',
        'weekdays': WeekdayField.WEEKDAY_CHOICES[:-3],
        'bars': bars
    })
