from datetime import timedelta

from django.contrib.auth.models import User
from django.db import models
from django.urls import reverse
from django.utils import formats
from django.utils.text import slugify
from ics import Event as IcsEvent, Organizer, DisplayAlarm, Geo

from studibars.settings import JSON_LD_BASE_URL


class Weekday(models.IntegerChoices):
    MONDAY = 1, 'Montag'
    TUESDAY = 2, 'Dienstag'
    WEDNESDAY = 3, 'Mittwoch'
    THURSDAY = 4, 'Donnerstag'
    FRIDAY = 5, 'Freitag'
    SATURDAY = 6, 'Samstag'
    SUNDAY = 7, 'Sonntag'


ENGLISH_WEEKDAYS = {
    Weekday.MONDAY: 'Monday',
    Weekday.TUESDAY: 'Tuesday',
    Weekday.WEDNESDAY: 'Wednesday',
    Weekday.THURSDAY: 'Thursday',
    Weekday.FRIDAY: 'Friday',
    Weekday.SATURDAY: 'Saturday',
    Weekday.SUNDAY: 'Sunday',
}


class WeekdayField(models.IntegerField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = Weekday
        super(WeekdayField, self).__init__(*args, **kwargs)


class Bar(models.Model):
    class OpenModel(models.IntegerChoices):
        WEEKLY = 1, 'Weekly'
        OPEN_135 = 2, '1. 3. 5.'

    name = models.CharField(unique=True, max_length=254)
    description = models.TextField(null=True, blank=True)
    instagram_id = models.CharField(null=True, blank=True, max_length=254)
    website = models.URLField(null=True, blank=True)
    menu_url = models.URLField(null=True, blank=True)
    day = WeekdayField()
    start_time = models.TimeField(default='21:00')
    end_time = models.TimeField(null=True, blank=True, help_text="Ungefähres Ende")
    open = models.IntegerField(choices=OpenModel, help_text="Sowas wie jede Woche, 1./3./5. Mittwoch",
                               default=OpenModel.WEEKLY)
    image = models.ImageField(upload_to="bars/", blank=True, null=True)
    city = models.CharField(max_length=50)
    zip_code = models.CharField(max_length=6)
    street = models.CharField(max_length=70, help_text="Straße und Hausnummer")
    latitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    longitude = models.DecimalField(max_digits=22, decimal_places=16, blank=True, null=True)
    tags = models.CharField(max_length=254, default="", help_text="Komma separierte Liste an Tags")

    def __str__(self):
        return self.name

    def has_tags(self):
        return len(self.tags) > 0

    def tag_list(self):
        if len(self.tags) > 0:
            items = self.tags.split(',')
            result = []
            for item in items:
                if '#' in item:
                    text, color = item.rsplit('#', 1)
                else:
                    text, color = item, "warning"
                result.append((text.strip(), color))
            return result
        return []

    def open_text(self):
        text = "Jeden "
        if self.open == self.OpenModel.OPEN_135:
            text += f"{self.OpenModel.OPEN_135.label} "
        text += f"{self.get_day_display()} ab {formats.localize(self.start_time)}"
        return text

    def day_text(self):
        if self.open == self.OpenModel.OPEN_135:
            return "1., 3. & 5. " + self.get_day_display()
        return "Wöchentlich"

    def json_ld_postal_address(self) -> dict:
        return {
            "@type": "PostalAddress",
            "streetAddress": self.street,
            "addressLocality": self.city,
            "addressRegion": "NRW",
            "postalCode": self.zip_code,
            "addressCountry": "DE",
        }

    def url_path(self):
        return reverse("bar_view", args=[self.id, slugify(self.name)])

    def to_json_ld(self) -> dict:
        json_ld = {
            "@context": "https://schema.org",
            "@type": "BarOrPub",
            "name": self.name,
            "address": self.json_ld_postal_address(),
            "priceRange": "$",
            "openingHoursSpecification": {
                "@type": "OpeningHoursSpecification",
                "dayOfWeek": ENGLISH_WEEKDAYS[self.day],
                "opens": str(self.start_time),
                "closes": str(self.end_time) or "02:00",
            },
            "url": JSON_LD_BASE_URL + self.url_path(),
        }
        if self.menu_url:
            json_ld["menu"] = self.menu_url
            json_ld["hasMenu"] = self.menu_url
        if self.longitude and self.latitude:
            json_ld["geo"] = {
                "@type": "GeoCoordinates",
                "latitude": float(self.latitude),
                "longitude": float(self.longitude),
            }
        if self.website:
            json_ld["sameAs"] = self.website
        return json_ld


class Event(models.Model):
    name = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    bar = models.ForeignKey(Bar, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    poster = models.FileField(upload_to="events/", null=True, blank=True)

    def to_ics_event(self) -> IcsEvent:
        ics_event = IcsEvent()
        ics_event.name = self.name
        ics_event.begin = self.start_date
        ics_event.end = self.end_date if self.end_date else self.start_date + timedelta(hours=4)
        ics_event.description = self.description
        ics_event.location = f"{self.bar.street}, {self.bar.zip_code} {self.bar.city}"
        if self.bar.latitude and self.bar.longitude:
            ics_event.geo = Geo(self.bar.latitude, self.bar.longitude)
        ics_event.status = "CONFIRMED"
        ics_event.uid = f"event-{self.id}@studibars-ac.de"
        ics_event.organizer = Organizer(common_name=self.bar.name, email="noreply@studibars-ac.de")

        # Add an alarm/reminder
        alarm = DisplayAlarm(trigger=timedelta(days=-1))
        ics_event.alarms.append(alarm)
        return ics_event

    def url_path(self):
        return reverse("event_view", args=[self.id, slugify(f"{self.name}-{self.bar.name}-{self.start_date.date()}")])

    def to_json_ld(self) -> dict:
        event = {
            "@context": "https://schema.org",
            "@type": "Event",
            "name": self.name,
            "description": self.description,
            "startDate": str(self.start_date),
            "endDate": str(self.end_date or self.start_date + timedelta(hours=5)),
            "eventStatus": "https://schema.org/EventScheduled",
            "eventAttendanceMode": "https://schema.org/OfflineEventAttendanceMode",
            "location": {
                "@type": "Place",
                "name": self.bar.name,
                "address": self.bar.json_ld_postal_address(),
            },
            "organizer": self.bar.to_json_ld(),
            "isAccessibleForFree": True,
            "url": JSON_LD_BASE_URL + self.url_path(),
        }
        if self.poster:
            event["image"] = self.poster.url
        return event

    def __str__(self):
        return self.name
