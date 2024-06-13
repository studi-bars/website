from django.contrib.auth import views as auth_views
from django.urls import path

from main import views

urlpatterns = [
    path('main', views.main_view, name='main'),
    path('ics/event/<int:event_id>/', views.download_event_ics, name='download_event_ics'),
]
