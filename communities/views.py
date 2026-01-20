from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import CommunityProfile, Tag, PersonProfile, Membership


class HomeView(TemplateView):
    """Strona główna"""
    template_name = 'communities/home.html'

class CommunityListView(ListView):
    """Lista wspólnot"""
    model = CommunityProfile
    template_name = 'communities/community_list.html'
    context_object_name = 'communities'
    paginate_by = 12  # 12 wspólnot na stronę

    def get_queryset(self):
        """Filtrowanie wspólnot"""
        # queryset = CommunityProfile.objects.filter(is_active=True).select_related('user')
        queryset = CommunityProfile.objects.filter(is_active=True)
        # Filtrowanie po mieście
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filtrowanie po denominacji
        denomination = self.request.GET.get('denomination')
        if denomination:
            queryset = queryset.filter(denomination=denomination)
        
        # Filtrowanie po tagach
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Wyszukiwanie po nazwie
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """Dodatkowe dane do template"""
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all()
        context['denominations'] = CommunityProfile.DENOMINATION_CHOICES
        return context
    
class CommunityDetailView(DetailView):
    """Szczegóły wspólnoty"""
    model = CommunityProfile
    template_name = 'communities/community_detail.html'
    context_object_name = 'community'
    
    def get_queryset(self):
        """Tylko aktywne wspólnoty"""
        # return CommunityProfile.objects.filter(is_active=True).select_related('user').prefetch_related('tags')
        return CommunityProfile.objects.filter(is_active=True).prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Dodaj członków do kontekstu"""
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.memberships.filter(
            is_active=True
        ).select_related('person__person_profile').order_by('-joined_date')
        return context

class ProfileView(LoginRequiredMixin, TemplateView):
    """
    Widok profilu zalogowanego użytkownika.
    
    Pokazuje:
    - Dane osobowe (PersonProfile)
    - Wspólnoty do których należy (memberships)
    - Wspólnoty którymi zarządza (owner/admin)
    
    LoginRequiredMixin = wymaga zalogowania
    """
    
    template_name = 'communities/profile_person.html'
    
    def get_context_data(self, **kwargs):
        """
        Przygotuj dane dla template.
        """
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Pobierz profil osoby (lub stwórz jeśli nie istnieje)
        # get_or_create zwraca tuple: (obiekt, czy_został_utworzony)
        profile, created = PersonProfile.objects.get_or_create(
            user=user,
            defaults={
                'first_name': user.first_name or user.username
            }
        )
        context['profile'] = profile
        
        # Pobierz wszystkie wspólnoty do których należy użytkownik
        context['memberships'] = user.memberships.filter(
            is_active=True
        ).select_related('community').order_by('-joined_date')
        
        # Pobierz wspólnoty którymi zarządza (owner lub admin)
        context['managed_communities'] = user.memberships.filter(
            is_active=True,
            role__in=['owner', 'admin']
        ).select_related('community')
        
        return context


class ProfileEditView(LoginRequiredMixin, UpdateView):
    """
    Widok edycji profilu osoby.
    
    UpdateView to generic view Django do edycji obiektów.
    Automatycznie generuje formularz i obsługuje POST.
    """
    
    model = PersonProfile
    template_name = 'communities/profile_edit.html'
    fields = ['first_name', 'last_name', 'city', 'bio', 'photo_url']
    success_url = reverse_lazy('communities:profile')
    
    def get_object(self, queryset=None):
        """
        Pobierz profil zalogowanego użytkownika.
        
        Nadpisujemy tę metodę żeby edytować profil CURRENT USER,
        a nie profil z parametru URL (jak normalnie w UpdateView).
        """
        profile, created = PersonProfile.objects.get_or_create(
            user=self.request.user,
            defaults={'first_name': self.request.user.username}
        )
        return profile
    
    def form_valid(self, form):
        """
        Wywoływane gdy formularz jest poprawnie wypełniony.
        """
        messages.success(self.request, 'Profil został zaktualizowany!')
        return super().form_valid(form)

# MOJA PROBA MAŁPOWANIA:
# class ProfileView(DetailView):
#     model = PersonProfile
#     template_name = 'communities/person_detail.html'
#     context_object_name = 'user_profile'

#     def get_queryset(self):
#         '''Tylko aktywni uzytkownicy'''
#         return PersonProfile.objects.filter(is_active=True).select_related('user').prefetch_related('tags')
    
#     def get_context_data(self, **kwargs):
#         context =  super().get_context_data(**kwargs)
#         context['members'] = self.object.membership.filter(is_active=True).select_related('person__person_profile').order_by('-joined_date')
#         return context
    
#     def get_template_names(self):
#         """
#         Wybierz template w zależności od typu użytkownika.
#         Aktualnie wszyscy to 'person', ale to pozostaje dla przyszłości.
#         """
#         if self.request.user.user_type == 'person':
#             return ['communities/profile_person.html']
#         # elif self.request.user.user_type == 'moderator':  # Przyszłość
#         #     return ['communities/profile_moderator.html']
#         else:
#             # Fallback (nie powinno się zdarzyć)
#             return ['communities/profile_person.html']
    
# ====================================================
## **Teraz templates - najprostsza wersja:**

# **Struktura folderów:**
# ```
# communities/
# └── templates/
#     └── communities/
#         ├── base.html           # Bazowy template
#         ├── home.html           # Strona główna
#         ├── community_list.html # Lista
#         └── community_detail.html # Szczegóły