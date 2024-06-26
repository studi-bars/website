# Generated by Django 5.0.3 on 2024-06-02 13:33

import django.db.models.deletion
import main.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Bar',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=254, unique=True)),
                ('description', models.TextField()),
                ('instagram_id', models.CharField(blank=True, max_length=254, null=True)),
                ('day', main.models.WeekdayField(choices=[(1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'), (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'), (7, 'Sunday')])),
                ('start_time', models.TimeField(default='21:00')),
                ('end_time', models.TimeField(blank=True, help_text='Ungefähres Ende', null=True)),
                ('open', models.CharField(help_text='Sowas wie jede Woche, 1./3./5. Mittwoch', max_length=254)),
                ('image', models.ImageField(blank=True, null=True, upload_to='bars/')),
                ('location', models.CharField(max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Event',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=254)),
                ('description', models.TextField(blank=True, null=True)),
                ('start_date', models.DateTimeField()),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('poster', models.FileField(blank=True, null=True, upload_to='events/')),
                ('bar', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='main.bar')),
            ],
        ),
    ]
