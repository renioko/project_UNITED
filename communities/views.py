from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.urls import reverse_lazy
from .models import CommunityProfile, Tag, PersonProfile, Membership


@login_required
@require_POST  # Tylko POST request (bezpieczeństwo - nie da się kliknąć w link GET)
def join_community(request, pk):
    """
    Dołącz do wspólnoty.

    Logika:
    - Sprawdź czy użytkownik NIE jest już członkiem
    - Stwórz Membership z rolą 'member'
    - Przekieruj z komunikatem sukcesu
    
    @login_required - wymaga zalogowania (przekierowuje do /accounts/login/)
    @require_POST - tylko POST (nie GET) - bezpieczeństwo CSRF
    """
    
    # Pobierz wspólnotę (lub 404 jeśli nie istnieje)
    community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
    
    # Sprawdź czy wspólnota akceptuje nowych członków (możesz dodać to pole później)
    # if not community.accepting_members:
    #     messages.error(request, 'Ta wspólnota nie przyjmuje obecnie nowych członków.')
    #     return redirect('communities:community_detail', pk=community.pk)

    # Sprawdź czy użytkownik ma PersonProfile
    if not hasattr(request.user, 'person_profile'):
        messages.error(
            request,
            'Musisz uzupełnić swój profil zanim dołączysz do wspólnoty.'
        )
        return redirect('communities:profile_edit')
    
    # Sprawdź czy użytkownik już jest członkiem
    already_member = Membership.objects.filter(
        person=request.user,
        community=community,
        is_active=True 
    ).exists()
    
    if already_member:
        # Już jest członkiem - nie dodawaj ponownie
        messages.warning(
            request, 
            f'Już należysz do wspólnoty "{community.name}".'
        )
    else:
        # Stwórz nowe członkostwo
        Membership.objects.create(
            person=request.user,
            community=community,
            role='member',  # Domyślnie zwykły członek
            is_active=True # 💡na przyszlosc - mozna zrobic False i aktywowac
        )
        
        messages.success(
            request,
            f'🎉 Gratulacje! Dołączyłeś do wspólnoty "{community.name}"!'
        )
    
    # Przekieruj z powrotem do profilu wspólnoty
    return redirect('communities:community_detail', pk=community.pk)


@login_required
@require_POST
def leave_community(request, pk):
    """
    Opuść wspólnotę.
    
    Logika:
    - Sprawdź czy użytkownik jest członkiem
    - Usuń lub dezaktywuj Membership
    - Przekieruj z komunikatem
    
    UWAGA: Owner (założyciel) nie może opuścić - musi najpierw przekazać uprawnienia!
    """
    
    community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
    
    # Sprawdź czy użytkownik jest członkiem
    try:
        membership = Membership.objects.get(
            person=request.user,
            community=community,
            is_active=True
        )
    except Membership.DoesNotExist:
        # Nie jest członkiem
        messages.warning(
            request,
            f'Nie należysz do wspólnoty "{community.name}".'
        )
        return redirect('communities:community_detail', pk=community.pk)
    
    # Sprawdź czy to nie owner/admin (nie mogą opuścić bez przekazania uprawnień)
    if membership.role in ['owner', 'admin']:
        messages.error(
            request,
            f'Nie możesz opuścić wspólnoty jako {membership.get_role_display()}. '
            f'Najpierw przekaż uprawnienia innemu członkowi lub skontaktuj się z administratorem.'
        )
        return redirect('communities:community_detail', pk=community.pk)
    
    # Opuść wspólnotę - usuń membership
    # OPCJA A: Całkowite usunięcie (bez historii)
    membership.delete()
    
    # OPCJA B: Dezaktywacja (zachowaj historię)
    # membership.is_active = False
    # membership.save()
    
    messages.info(
        request,
        f'Opuściłeś wspólnotę "{community.name}". Możesz dołączyć ponownie w każdej chwili.'
    )
    
    # Przekieruj do listy wspólnot (bo już nie jest członkiem)
    return redirect('communities:community_list')

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
        return CommunityProfile.objects.filter(is_active=True).select_related('created_by').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Dodaj członków i status członkostwa do kontekstu"""
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.memberships.filter(
            is_active=True
        ).select_related('person__person_profile').order_by('-joined_date')

        # NOWE - sprawdź czy zalogowany użytkownik jest członkiem
        if self.request.user.is_authenticated:
            try:
                # Spróbuj znaleźć membership
                membership = self.object.memberships.get(
                    person=self.request.user,
                    is_active=True
                )
                context['user_membership'] = membership
                context['is_member'] = True
                context['can_leave'] = membership.role not in ['owner', 'admin']
            except Membership.DoesNotExist:
                # Nie jest członkiem
                context['user_membership'] = None
                context['is_member'] = False
                context['can_leave'] = False
        else:
            # Użytkownik niezalogowany
            context['user_membership'] = None
            context['is_member'] = False
            context['can_leave'] = False
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

