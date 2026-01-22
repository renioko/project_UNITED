"""
Mixins dla systemu uprawnień wspólnot.

Mixins to klasy pomocnicze które można "domieszać" do widoków
aby dodać im określoną funkcjonalność (np. sprawdzanie uprawnień).
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import CommunityProfile


class CommunityPermissionMixin(LoginRequiredMixin):
    """
    Bazowy mixin sprawdzający uprawnienia do wspólnoty.
    
    Używany w widokach które wymagają określonych uprawnień
    (edycja profilu, zarządzanie członkami, itp.)
    
    Dziedziczy po LoginRequiredMixin - wymaga zalogowania.
    """
    
    # Które role mają dostęp? (nadpisz w konkretnym widoku)
    required_roles = []  # np. ['owner', 'admin']
    
    def dispatch(self, request, *args, **kwargs):
        """
        Metoda wywoływana przed każdym request.
        Tu sprawdzamy uprawnienia.
        """
        # Pobierz wspólnotę z URL (pk w kwargs)
        self.community = get_object_or_404(
            CommunityProfile,
            pk=self.kwargs.get('pk'),
            is_active=True
        )
        
        # Sprawdź uprawnienia
        if not self.has_permission():
            raise PermissionDenied("Nie masz uprawnień do zarządzania tą wspólnotą.")
        
        return super().dispatch(request, *args, **kwargs)
    
    def has_permission(self):
        """
        Sprawdź czy użytkownik ma wymagane uprawnienia.
        """
        # Superuser ma wszystkie uprawnienia
        if self.request.user.is_superuser:
            return True
        
        # Sprawdź czy użytkownik ma odpowiednią rolę we wspólnocie
        return self.community.memberships.filter(
            person=self.request.user,
            role__in=self.required_roles,
            is_active=True
        ).exists()
    
    def get_context_data(self, **kwargs):
        """
        Dodaj wspólnotę do kontekstu (żeby była dostępna w template).
        """
        context = super().get_context_data(**kwargs)
        context['community'] = self.community
        return context


class CommunityOwnerRequiredMixin(CommunityPermissionMixin):
    """
    Mixin wymagający roli OWNER.
    Używaj dla najbardziej wrażliwych operacji (usunięcie wspólnoty, zmiana ownera).
    """
    required_roles = ['owner']


class CommunityAdminRequiredMixin(CommunityPermissionMixin):
    """
    Mixin wymagający roli OWNER lub ADMIN.
    Używaj dla operacji zarządzania (edycja profilu, zarządzanie członkami).
    """
    required_roles = ['owner', 'admin']


class CommunityLeaderRequiredMixin(CommunityPermissionMixin):
    """
    Mixin wymagający roli OWNER, ADMIN lub LEADER.
    Używaj dla operacji moderacji (zatwierdzanie członków, tworzenie wydarzeń).
    
    ZMIANA: Leader teraz ma więcej uprawnień:
    - Może edytować profil wspólnoty
    - Może zarządzać członkami (usuwać zwykłych członków)
    - NIE może zmieniać ról (to tylko owner/admin)
    """
    required_roles = ['owner', 'admin', 'leader']

class CommunityMemberManagementMixin(CommunityPermissionMixin):
    """
    Mixin dla zarządzania członkami.
    
    Dostęp: owner, admin, leader
    
    Leader może:
    - Usuwać zwykłych członków
    - Widzieć listę członków
    
    Leader NIE może:
    - Zmieniać ról
    - Usuwać admin/owner
    """
    required_roles = ['owner', 'admin', 'leader']