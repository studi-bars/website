from django.contrib.auth import views as auth_views
from django.urls import path

from main import views

urlpatterns = [
    path('main', views.main_view, name='main'),
    path('ics/event/<int:event_id>/', views.download_event_ics, name='download_event_ics'),
    path('ics/bar/events/<int:bar_id>/', views.download_bar_events_ics, name='download_bar_events_ics'),
    path('bar/<int:bar_id>/<name>/', views.bar_view, name='bar_view'),
    path('event/<int:event_id>/<name>/', views.event_view, name='event_view'),

    path('robots.txt', views.robots, name='robots'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]
