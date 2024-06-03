from django.contrib import admin

from main.models import Bar, Event


@admin.register(Bar)
class BarAdmin(admin.ModelAdmin):
    pass


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    pass
