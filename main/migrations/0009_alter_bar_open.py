# Generated by Django 5.0.6 on 2024-09-02 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0008_event_emoji'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bar',
            name='open',
            field=models.IntegerField(choices=[(1, 'Weekly'), (2, '1. 3. 5.'), (3, '1. und 3.')], default=1, help_text='Sowas wie jede Woche, 1./3./5. Mittwoch'),
        ),
    ]
