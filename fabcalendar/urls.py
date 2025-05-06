from django.urls import path
from . import views

app_name = 'fabcalendar'

urlpatterns = [
    path('', views.CalendarView.as_view(), name='calendar'),
    path('events/', views.get_events, name='get_events'),
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
] 