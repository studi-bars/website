from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from main import views

urlpatterns = [
    path('main', views.main_view, name='main'),
    re_path(r"^ics/event/.*(?P<event_id>[0-9]+)/$", views.download_event_ics, name='download_event_ics'),
    re_path(r"^ics/bar/events/.*(?P<bar_id>[0-9]+)/$", views.download_bar_events_ics, name='download_bar_events_ics'),
    path('bar/<int:bar_id>/<name>/', views.bar_view, name='bar_view'),
    path('event/<int:event_id>/<name>/', views.event_view, name='event_view'),

    path('robots.txt', views.robots, name='robots'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]
