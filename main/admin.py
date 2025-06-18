from time import timezone

from django.contrib import admin
from django.contrib.admin import SimpleListFilter, TabularInline
from django.utils import timezone

from main.models import Bar, Event, BarImage, SpecialDrink


class BarImageInline(admin.TabularInline):
    model = BarImage
    extra = 1  # Number of empty forms to display
    fields = ['image', 'order']  # Include the order field
    sortable_field_name = 'order'  # Enable ordering by this field


@admin.register(Bar)
class BarAdmin(admin.ModelAdmin):
    inlines = [BarImageInline]


class FutureEventsFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'Event Zeit'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'time'

    def lookups(self, request, model_admin):
        return (
            ('0', 'Kommende Events'),
            ('1', 'Alte Events')
        )

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        """
        if self.value() == "0":
            return queryset.filter(start_date__gte=timezone.now().date())
        if self.value() == "1":
            return queryset.filter(start_date__lt=timezone.now().date())

        return queryset


class SpecialDrinkInline(TabularInline):
    model = SpecialDrink


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'bar')
    ordering = ('-start_date',)
    list_filter = ('bar', FutureEventsFilter,)
    inlines = [SpecialDrinkInline]
