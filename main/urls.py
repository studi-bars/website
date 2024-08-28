from django.contrib.auth import views as auth_views
from django.urls import path, re_path

from main import views

urlpatterns = [
    path('main', views.main_view, name='main'),
    path('<bar>/<name>--<int:event_id>.ics', views.download_event_ics, name='download_event_ics'),
    # Folgenden beide Pfade nicht mehr ändern/löschen da diese aktiv in Kalendern eingebunden sind:
    re_path(r"^ics/bar/events/.*(?P<bar_id>[0-9]+)/$", views.download_bar_events_ics, name='download_bar_events_ics_old_keep'),
    path('<name>/events-<int:bar_id>.ics', views.download_bar_events_ics, name='download_bar_events_ics'),
    path('bar/<int:bar_id>/<name>/', views.bar_view_id, name='bar_view_old'),
    path('<name>/', views.bar_view_name, name='bar_view'),
    path('event/<int:event_id>/<name>/', views.event_view, name='event_view_old'),
    path('<bar>/<name>--<int:event_id>/', views.event_view, name='event_view'),

    path('robots.txt', views.robots, name='robots'),
    path('sitemap.xml', views.sitemap, name='sitemap'),
]
