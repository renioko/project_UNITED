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
    # Tworzenie wspólnoty
    path('communities/create/', views.CommunityCreateView.as_view(), name='community_create'),
    # ... join/leave ...
    path('communities/<int:pk>/join/', views.join_community, name='join_community'),
    path('communities/<int:pk>/leave/', views.leave_community, name='leave_community'),
    # Zarządzanie wspólnotą (tylko owner/admin)
    path('communities/<int:pk>/edit/', views.CommunityEditView.as_view(), name='community_edit'),
    path('communities/<int:pk>/manage/', views.CommunityManageView.as_view(), name='community_manage'),
    path('communities/<int:pk>/member/<int:membership_id>/change-role/', views.change_member_role, name='change_member_role'),
    path('communities/<int:pk>/member/<int:membership_id>/remove/', views.remove_member, name='remove_member'),
]
