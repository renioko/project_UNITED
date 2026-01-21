from django.urls import path
from . import views

app_name = 'communities'

urlpatterns = [
    # path('', views.home, name='home'),  # Strona główna
    # path('communities/', views.community_list, name='community_list'),  # Lista
    # path('communities/<int:pk>/', views.community_detail, name='community_detail'),  # Szczegóły
    path('', views.HomeView.as_view(), name='home'), # Strona główna
    path('communities/', views.CommunityListView.as_view(), name='community_list'),  # Lista
    path('communities/<int:pk>/', views.CommunityDetailView.as_view(), name='community_detail'), # Szczegóły
    path('profile/', views.ProfileView.as_view(), name='profile'),
    path('profile/edit/', views.ProfileEditView.as_view(), name='profile_edit'),
    path('communities/<int:pk>/join/', views.join_community, name='join_community'),
    path('communities/<int:pk>/leave/', views.leave_community, name='leave_community'),
]
