from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    path('', views.home, name='home'),  # Strona główna
    path('communities/', views.community_list, name='community_list'),  # Lista
    path('communities/<int:pk>/', views.community_detail, name='community_detail'),  # Szczegóły
]