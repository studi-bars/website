from rest_framework import serializers

from main.models import Bar, Event, SpecialDrink


class BarSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bar
        fields = '__all__'


class SpecialDrinkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecialDrink
        fields = '__all__'


class EventSerializer(serializers.ModelSerializer):
    special_drinks = SpecialDrinkSerializer(many=True, read_only=True)

    class Meta:
        model = Event
        fields = '__all__'
