from django.contrib.auth.models import User
from django.db import models


class Weekday(models.IntegerChoices):
    MONDAY = 1, 'Montag'
    TUESDAY = 2, 'Dienstag'
    WEDNESDAY = 3, 'Mittwoch'
    THURSDAY = 4, 'Donnerstag'
    FRIDAY = 5, 'Freitag'
    SATURDAY = 6, 'Samstag'
    SUNDAY = 7, 'Sonntag'


class WeekdayField(models.IntegerField):

    def __init__(self, *args, **kwargs):
        kwargs['choices'] = Weekday
        super(WeekdayField, self).__init__(*args, **kwargs)


class Bar(models.Model):
    class OpenModel(models.IntegerChoices):
        WEEKLY = 1, 'Weekly'
        OPEN_135 = 2, '1./3./5.'

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

    def __str__(self):
        return self.name


class Event(models.Model):
    name = models.CharField(max_length=254)
    description = models.TextField(null=True, blank=True)
    bar = models.ForeignKey(Bar, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField(null=True, blank=True)
    poster = models.FileField(upload_to="events/", null=True, blank=True)

    def __str__(self):
        return self.name
