from django.urls import path
from . import views

app_name = 'activities'

urlpatterns = [
    path('events/create/', views.EventCreateView.as_view(), name='event_create'),
    path('events/<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('events/<int:pk>/follow/', views.follow_event, name='follow_event'),
    path('communities/<int:pk>/follow/', views.follow_community, name='follow_community'),
    path('announcements/create/', views.AnnouncementCreateView.as_view(), name='announcement_create'),
]
