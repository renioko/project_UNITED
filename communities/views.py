from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView, DeleteView, View
from django.urls import reverse_lazy
from .models import CommunityProfile, Tag, PersonProfile, Membership
from .forms import CommunityCreateForm, CommunityEditForm
from .mixins import CommunityAdminRequiredMixin, CommunityOwnerRequiredMixin, CommunityLeaderRequiredMixin
from activities.querysets import get_events_for_user, get_announcements_for_user

import json
from django.conf import settings

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
    template_name = 'communities/community_list2.html'
    context_object_name = 'communities'
    paginate_by = 12  # 12 wspólnot na stronę

    def get_queryset(self):
        """
        Filtrowanie wspólnot na podstawie parametrów GET.

        Proste wyszukiwanie - jedno pole szuka po wszystkim.

        Wyszukiwanie zaawansowane - bsługuje:
        - search: wyszukiwanie po nazwie i opisie
        - city: filtrowanie po mieście
        - denomination: filtrowanie po denominacji
        - tags: filtrowanie po tagach (można wybrać wiele)
        """

        queryset = CommunityProfile.objects.filter(is_active=True).select_related('created_by').prefetch_related('tags')

        # Wyszukiwanie po nazwie i opisie
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search) |
                Q(city__icontains=search) |
                Q(tags__name__icontains=search)  # Szuka też w tagach!
            ).distinct()

    # ZAAWANSOWANE wyszukiwanie
        # Filtrowanie po mieście
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filtrowanie po denominacji
        denomination = self.request.GET.get('denomination')
        if denomination:
            queryset = queryset.filter(denomination=denomination)
        
        # Filtrowanie tag (tylko jeden z dropdown)
        tag = self.request.GET.get('tag')
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        # # Filtrowanie po tagach
        # tag_slug = self.request.GET.get('tag')
        # if tag_slug:
        #     queryset = queryset.filter(tags__slug=tag_slug)
        
        # Filtrowanie po tagach - WYBÓR WIELU -nieaktywne (można wybrać wiele)
        # Pobierz listę ID tagów z GET (może być wiele)
        tag_ids = self.request.GET.getlist('tags')  # getlist! nie get
        if tag_ids:
            # Filtruj wspólnoty które mają KTÓRYKOLWIEK z wybranych tagów
            queryset = queryset.filter(tags__id__in=tag_ids).distinct()
        
        # Wyszukiwanie po nazwie
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        # Sortowanie (opcjonalnie)
        sort_by = self.request.GET.get('sort', '-created_at')
        queryset = queryset.order_by(sort_by)

        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """Dodatkowe dane do template"""
        context = super().get_context_data(**kwargs)

        # Lista wszystkich tagów (dla formularza)
        context['all_tags'] = Tag.objects.all().order_by('name')
        # context['tags'] = Tag.objects.all()
        context['denominations'] = CommunityProfile.DENOMINATION_CHOICES

                # Zachowaj parametry wyszukiwania (dla paginacji i formularza)
        context['current_search'] = self.request.GET.get('search', '')
        context['current_city'] = self.request.GET.get('city', '')
        context['current_denomination'] = self.request.GET.get('denomination', '')
        context['selected_tags'] = self.request.GET.getlist('tags')

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
        context = super().get_context_data(**kwargs)
        
        # Członkowie wspólnoty
        context['members'] = self.object.memberships.filter(
            is_active=True
        ).select_related('person__person_profile').order_by('-joined_date')

        if self.request.user.is_authenticated:
            # Status członkostwa
            try:
                membership = self.object.memberships.get(
                    person=self.request.user,
                    is_active=True
                )
                context['user_membership'] = membership
                context['is_member'] = True
                context['can_leave'] = membership.role not in ['owner', 'admin']
            except Membership.DoesNotExist:
                context['user_membership'] = None
                context['is_member'] = False
                context['can_leave'] = False

            # Status obserwowania
            from activities.models import Follow
            context['is_following'] = Follow.objects.filter(
                user=self.request.user,
                community=self.object,
            ).exists()

        else:
            context['user_membership'] = None
            context['is_member'] = False
            context['can_leave'] = False
            context['is_following'] = False

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
    fields = ['first_name', 'last_name', 'city', 'bio', 'avatar']
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

class CommunityCreateView(LoginRequiredMixin, CreateView):
    """
    Widok tworzenia nowej wspólnoty.
    
    CreateView to generic view Django do tworzenia obiektów.
    Automatycznie:
    - Wyświetla formularz (GET)
    - Obsługuje zapisywanie (POST)
    - Waliduje dane
    - Przekierowuje po sukcesie
    
    LoginRequiredMixin = tylko zalogowani użytkownicy mogą tworzyć wspólnoty
    """
    
    model = CommunityProfile
    form_class = CommunityCreateForm
    template_name = 'communities/community_create.html'
    
    def form_valid(self, form):
        """
        Wywoływane gdy formularz jest poprawnie wypełniony.
        
        Tu ustawiamy created_by (twórca wspólnoty) na current user.
        """
        
        # Nie zapisuj jeszcze do bazy (commit=False)
        community = form.save(commit=False)
        
        #Ustaw full address:
        # community.full_address = f"{community.address}, {community.city}, {community.country}"

        # Ustaw twórcę na zalogowanego użytkownika
        community.created_by = self.request.user
        
        # Teraz zapisz do bazy
        community.save()
        
        # Zapisz relacje ManyToMany (tagi)
        # WAŻNE: form.save_m2m() musi być AFTER save()
        form.save_m2m()
        
        # SIGNAL automatycznie utworzy Membership z rolą 'owner'!
        # (sprawdź communities/signals.py)
        
        # Komunikat sukcesu
        messages.success(
            self.request,
            f'🎉 Wspólnota "{community.name}" została utworzona! Jesteś jej właścicielem (owner).'
        )
        
        # Przekieruj do profilu nowo utworzonej wspólnoty
        self.success_url = reverse_lazy('communities:community_detail', kwargs={'pk': community.pk})
        
        return super().form_valid(form)
    
    def form_invalid(self, form):
        """
        Wywoływane gdy formularz ma błędy.
        """
        messages.error(
            self.request,
            'Wystąpiły błędy w formularzu. Sprawdź poprawność danych.'
        )
        return super().form_invalid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        return context
    
class CommunityEditView(CommunityLeaderRequiredMixin, UpdateView):
    """
    Edycja profilu wspólnoty.
    
    Dostęp: owner, admin, leader 
    """
    model = CommunityProfile
    form_class = CommunityEditForm
    template_name = 'communities/community_edit.html'
    
    def get_object(self, queryset=None):
        """Pobierz wspólnotę (już mamy w self.community z mixina)"""
        return self.community
    
    def get_success_url(self):
        """Przekieruj do profilu wspólnoty po sukcesie"""
        return reverse_lazy('communities:community_detail', kwargs={'pk': self.community.pk})
    
    # NIE WIEM CZY TO KONIECZNE?? ❓❓
    #  UWAGA: Django automatycznie obsługuje request.FILES w UpdateView, więc teoretycznie post() nie jest konieczne, ALE dodaję go dla pewności i czytelności.
    # def post(self, request, *args, **kwargs):
    #         """
    #         Obsługa POST z plikami.
            
    #         WAŻNE: request.FILES jest potrzebne do uploadu obrazków!
    #         """
    #         self.object = self.get_object()
    #         form = self.get_form()
            
    #         if form.is_valid():
    #             return self.form_valid(form)
    #         else:
    #             return self.form_invalid(form)

    def form_valid(self, form):
        """Komunikat sukcesu"""
        messages.success(self.request, f'✅ Profil wspólnoty "{self.community.name}" został zaktualizowany.')
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['GOOGLE_MAPS_API_KEY'] = settings.GOOGLE_MAPS_API_KEY
        return context

class CommunityManageView(CommunityLeaderRequiredMixin, TemplateView):
    """
    Dashboard zarządzania wspólnotą.
    
    Pokazuje:
    - Lista członków z możliwością zarządzania
    - Statystyki
    - Szybkie akcje
    
    Dostęp: owner, admin, leader
    """
    template_name = 'communities/community_manage.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Lista członków pogrupowana po rolach
        context['owners'] = self.community.memberships.filter(
            role='owner', is_active=True
        ).select_related('person__person_profile')
        
        context['admins'] = self.community.memberships.filter(
            role='admin', is_active=True
        ).select_related('person__person_profile')
        
        context['leaders'] = self.community.memberships.filter(
            role__in=['leader', 'service_leader'], is_active=True
        ).select_related('person__person_profile')
        
        context['members'] = self.community.memberships.filter(
            role='member', is_active=True
        ).select_related('person__person_profile')
        
        # Sprawdź rolę current user (co może robić)
        user_membership = self.community.memberships.filter(
            person=self.request.user, is_active=True
        ).first()
        
        context['user_membership'] = user_membership
        context['is_owner'] = user_membership and user_membership.role == 'owner'
        context['is_admin'] = user_membership and user_membership.role in ['owner', 'admin']
        context['is_leader'] = user_membership and user_membership.role in ['owner', 'admin', 'leader']

        # Statystyki
        context['total_members'] = self.community.get_member_count()
        
        return context


@login_required
@require_POST
def change_member_role(request, pk, membership_id):
    """
    Zmiana roli członka wspólnoty.
    
    Logika uprawnień:
    - Owner może zmieniać role wszystkim (włącznie z nadaniem owner)
    - Admin może zmieniać role do poziomu leader (NIE może nadać admin/owner)
    - Leader nie może zmieniać ról
    
    pk = ID wspólnoty
    membership_id = ID członkostwa do zmiany
    """
    
    # Pobierz wspólnotę
    community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
    
    # Pobierz członkostwo które chcemy zmienić
    membership = get_object_or_404(
        Membership,
        pk=membership_id,
        community=community,
        is_active=True
    )
    
    # Pobierz członkostwo current user (sprawdzamy jego uprawnienia)
    try:
        user_membership = Membership.objects.get(
            person=request.user,
            community=community,
            is_active=True
        )
    except Membership.DoesNotExist:
        messages.error(request, 'Nie jesteś członkiem tej wspólnoty.')
        return redirect('communities:community_detail', pk=pk)
    
    # Pobierz nową rolę z POST
    new_role = request.POST.get('role')
    
    # WALIDACJA UPRAWNIEŃ
    
    # Nie można zmienić roli samemu sobie
    if membership.person == request.user:
        messages.error(request, 'Nie możesz zmienić własnej roli. Poproś innego admina.')
        return redirect('communities:community_manage', pk=pk)
    
    # NOWE: Leader NIE może zmieniać ról
    if user_membership.role == 'leader':
        messages.error(
            request,
            'Jako lider nie masz uprawnień do zmiany ról. '
            'Role może zmieniać tylko właściciel lub administrator.'
        )
        return redirect('communities:community_manage', pk=pk)

    # Owner może wszystko
    if user_membership.role == 'owner':
        # Owner może nadać każdą rolę
        if new_role in dict(Membership.ROLE_CHOICES):
            
            # SPECJALNY PRZYPADEK: Nadawanie owner
            if new_role == 'owner':
                # Ostrzeżenie - teraz będzie dwóch ownerów
                messages.warning(
                    request,
                    f'⚠️ {membership.person.username} został właścicielem (owner). '
                    f'Teraz jest dwóch właścicieli tej wspólnoty.'
                )
            
            membership.role = new_role
            membership.save()
            
            messages.success(
                request,
                f'✅ Zmieniono rolę {membership.person.username} na {membership.get_role_display()}.'
            )
        else:
            messages.error(request, 'Nieprawidłowa rola.')
    
    # Admin może zmieniać do leader (NIE admin/owner)
    elif user_membership.role == 'admin':
        if new_role in ['member', 'service_leader', 'leader']:
            membership.role = new_role
            membership.save()
            
            messages.success(
                request,
                f'✅ Zmieniono rolę {membership.person.username} na {membership.get_role_display()}.'
            )
        else:
            messages.error(
                request,
                'Jako administrator możesz nadawać role tylko do poziomu Leader. '
                'Role Admin/Owner może nadać tylko właściciel.'
            )
    
    else:
        # Ani owner ani admin - brak uprawnień
        messages.error(request, 'Nie masz uprawnień do zmiany ról.')
    
    return redirect('communities:community_manage', pk=pk)


@login_required
@require_POST
def remove_member(request, pk, membership_id):
    """
    Usunięcie członka ze wspólnoty.
    
    Dostęp: owner, admin
    
    - Owner/Admin NIE mogą usunąć samych siebie.
    - Leader może usunąć tylko zwykłych członków (nie admin/leader/owner)
    - Owner NIE może być usunięty (musi sam opuścić lub przekazać uprawnienia).
    """
    
    community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
    
    membership = get_object_or_404(
        Membership,
        pk=membership_id,
        community=community,
        is_active=True
    )
        # Pobierz członkostwo current user
    try:
        user_membership = Membership.objects.get(
            person=request.user,
            community=community,
            is_active=True
        )
    except Membership.DoesNotExist:
        messages.error(request, 'Nie jesteś członkiem tej wspólnoty.')
        return redirect('communities:community_detail', pk=pk)
    
    # Sprawdź uprawnienia - owner/admin/leader
    if user_membership.role not in ['owner', 'admin', 'leader']:
        messages.error(request, 'Nie masz uprawnień do zarządzania członkami.')
        return redirect('communities:community_detail', pk=pk)

    # # Sprawdź uprawnienia current user
    # if not community.user_can_edit(request.user):
    #     messages.error(request, 'Nie masz uprawnień do zarządzania członkami.')
    #     return redirect('communities:community_detail', pk=pk)
    
    # WALIDACJA
    
    # Nie można usunąć samego siebie (użyj "Opuść wspólnotę")
    if membership.person == request.user:
        messages.error(
            request,
            'Nie możesz usunąć samego siebie. Użyj przycisku "Opuść wspólnotę".'
        )
        return redirect('communities:community_manage', pk=pk)
    
    # Nie można usunąć owner (owner musi sam opuścić lub przekazać uprawnienia)
    if membership.role == 'owner':
        messages.error(
            request,
            'Nie można usunąć właściciela (owner). '
            'Właściciel musi sam opuścić wspólnotę lub przekazać uprawnienia.'
        )
        return redirect('communities:community_manage', pk=pk)
    
    # NOWE: Leader może usunąć tylko zwykłych członków (nie admin/leader)
    if user_membership.role == 'leader': 
        if membership.role in ['admin', 'leader', 'service_leader']:
            messages.error(
                request,
                'Jako lider możesz usuwać tylko zwykłych członków. '
                'Administratorów i innych liderów może usunąć tylko właściciel lub administrator.'
            )
            return redirect('communities:community_manage', pk=pk)

    # Usuń członka
    member_name = membership.person.username
    membership.delete()
    
    messages.success(
        request,
        f'✅ Użytkownik {member_name} został usunięty ze wspólnoty.'
    )
    
    return redirect('communities:community_manage', pk=pk)

# ===========================================================================
# DASHBOARD - dodaj ten import na górze pliku views.py:
# from activities.querysets import get_announcements_for_user, get_events_for_user
# ===========================================================================

class DashboardView(LoginRequiredMixin, View):
    template_name = 'communities/dashboard.html'

    def get(self, request):
        user = request.user

        # Wspólnoty użytkownika
        my_memberships = Membership.objects.filter(
            person=user,
            is_active=True,
        ).select_related('community').order_by('role')

        # Nadchodzące wydarzenia (z querysets.py)
        from activities.querysets import get_events_for_user, get_announcements_for_user
        from django.utils import timezone

        upcoming_events = get_events_for_user(user).filter(
            date_start__gte=timezone.now()
        ).order_by('date_start')[:5]

        # Najnowsze ogłoszenia
        recent_announcements = get_announcements_for_user(user).order_by(
            '-created_at'
        )[:5]

        context = {
            'my_memberships': my_memberships,
            'upcoming_events': upcoming_events,
            'recent_announcements': recent_announcements,
        }
        return render(request, self.template_name, context)
    
class CommunityMapView(View):
    """
    Widok mapy wspólnot.
    GET /communities/map/ → strona z mapą
    GET /communities/map/data/ → JSON z danymi wspólnot (dla filtrowania AJAX)
    """
    template_name = 'communities/community_map2.html'
    # template_name = 'communities/community_map_with_clustering.html'
    def get(self, request): 
        # musze ustalic lokation, wokół ktorego szukam/filtruje lokalizacje wspolnot
        # musze przefiltrowac lokalizacje współnot, które sa w obrebie wyszukiwania
        # natstepnie przefiltrowac je przez tagi

        # Pobierz wszystkie aktywne wspólnoty z lokalizacją (❗trzeba zrobic cache❓)
        communities = CommunityProfile.objects.filter(
                    is_active=True,
                    latitude__isnull=False,
                    longitude__isnull=False,
                )

        # Filtrowanie po tagach (opcjonalne)
        tag_slug = request.GET.get('tag')
        if tag_slug:
            communities = communities.filter(tags__slug=tag_slug)

        # Optymalizacja: tylko potrzebne pola
        communities = communities.prefetch_related('tags').only(
            'id', 'name', 'city', 'latitude', 'longitude', 
            'denomination', 'description', 'logo'
        )[:500]
        # communities = communities.prefetch_related('tags')[:500]

        # Przygotuj dane JSON dla mapy
        communities_json = []
        for c in communities:
            communities_json.append({
                'id': c.pk,
                'name': c.name,
                'city': c.city,
                'lat': float(c.latitude) if c.latitude else None,
                'lng': float(c.longitude) if c.longitude else None,
                'denomination': c.get_denomination_display(),
                'tags': [t.name for t in c.tags.all()],
                'logo': c.logo.url if c.logo else None,
                # 'url': f'/communities/{c.pk}/',
                'url': c.get_absolute_url(),
                'description': c.description[:100] + '...' if len(c.description) > 100 else c.description,
            })

        # Wszystkie tagi do filtrowania
        all_tags = Tag.objects.filter(
            communities__is_active=True,
            communities__latitude__isnull=False,
        ).distinct()

        context = {
            'communities_json': communities_json,
            'all_tags': all_tags,
            'selected_tag': tag_slug,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }
        return render(request, self.template_name, context)

        # Przyklad lokalizacji
        # def get(self, request)
        # community_location = CommunityProfile.objects.filter(# tutaj ładowac lokalizacje)
        # context = {
        #     'community_location': community_location,
        #     }
        # return render(request, template_name='community_map.html', context='context') 