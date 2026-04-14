from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, DetailView
from django.urls import reverse_lazy

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from communities.models import CommunityProfile, Membership
from .models import Follow, Event, EventCommunity, EventRole
from .forms import EventCreateForm

class EventCreateView(LoginRequiredMixin, CreateView):
    """
    Formularz tworzenia nowego wydarzenia.

    Dostęp: owner, admin, leader, service_leader dowolnej wspólnoty.
    Zwykły member nie może tworzyć wydarzeń.
    """
    model = Event
    form_class = EventCreateForm
    template_name = 'activities/event_create.html'
    success_url = reverse_lazy('communities:dashboard')

    def dispatch(self, request, *args, **kwargs):
        """Sprawdź czy użytkownik ma uprawnienia do tworzenia eventu."""
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Sprawdź czy użytkownik ma odpowiednią rolę w jakiejkolwiek wspólnocie
        can_create = Membership.objects.filter(
            person=request.user,
            role__in=['owner', 'admin', 'leader', 'service_leader'],
            is_active=True,
        ).exists()

        if not can_create:
            messages.error(
                request,
                'Tylko liderzy i administratorzy wspólnot mogą tworzyć wydarzenia.'
            )
            return redirect('communities:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        """Przekaż usera do formularza - potrzebne do filtrowania wspólnot."""
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def form_valid(self, form):
        # Zapisz event
        event = form.save(commit=False)
        event.created_by = self.request.user
        event.save()
        form.save_m2m()  # Zapisz M2M (tagi itp. jeśli będą)

        # Ustaw główną wspólnotę organizującą (owner)
        owner_community = form.cleaned_data.get('owner_community')
        if owner_community:
            EventCommunity.objects.create(
                event=event,
                community=owner_community,
                role='owner',
            )

        # Ustaw współorganizatorów
        co_organizers = form.cleaned_data.get('co_organizer_communities')
        if co_organizers:
            for community in co_organizers:
                if community != owner_community:
                    EventCommunity.objects.create(
                        event=event,
                        community=community,
                        role='co_organizer',
                    )

        # Twórca eventu dostaje rolę owner eventu
        EventRole.objects.create(
            event=event,
            user=self.request.user,
            role='owner',
        )

        messages.success(request=self.request, message=f'Wydarzenie "{event.title}" zostało utworzone!')
        return redirect(self.success_url)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Wspólnoty w których user ma odpowiednią rolę
        context['my_communities'] = CommunityProfile.objects.filter(
            memberships__person=self.request.user,
            memberships__role__in=['owner', 'admin', 'leader', 'service_leader'],
            memberships__is_active=True,
        )
        return context


class EventDetailView(DetailView):
    """Widok szczegółu wydarzenia."""
    model = Event
    template_name = 'activities/event_detail.html'
    context_object_name = 'event'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        event = self.object
        user = self.request.user

        context['organizers'] = event.eventcommunity_set.select_related('community')
        context['coordinators'] = event.get_coordinators()
        context['announcements'] = event.announcements.filter(
            is_public=True
        ) if not user.is_authenticated else event.announcements.all()

        if user.is_authenticated:
            context['can_manage'] = event.user_can_manage(user)
            context['is_following'] = event.followers.filter(user=user).exists()

        return context
    

@login_required
@require_POST
def follow_community(request, pk):
    """Obserwuj lub przestań obserwować wspólnotę."""
    community = get_object_or_404(CommunityProfile, pk=pk)
    user = request.user

    # Nie możesz obserwować wspólnoty której jesteś członkiem
    is_member = community.memberships.filter(
        person=user,
        is_active=True,
    ).exists()

    if is_member:
        messages.info(request, 'Jesteś członkiem tej wspólnoty – nie musisz jej obserwować.')
        return redirect('communities:community_detail', pk=pk)

    # Toggle - jeśli obserwuje to przestań, jeśli nie to zacznij
    follow, created = Follow.objects.get_or_create(
        user=user,
        community=community,
    )

    if created:
        messages.success(request, f'Obserwujesz teraz wspólnotę {community.name}.')
    else:
        follow.delete()
        messages.info(request, f'Przestałeś obserwować wspólnotę {community.name}.')

    return redirect('communities:community_detail', pk=pk)


@login_required
@require_POST
def follow_event(request, pk):
    """Obserwuj lub przestań obserwować wydarzenie."""
    event = get_object_or_404(Event, pk=pk)
    user = request.user

    # Toggle
    follow, created = Follow.objects.get_or_create(
        user=user,
        event=event,
    )

    if created:
        messages.success(request, f'Obserwujesz teraz wydarzenie "{event.title}".')
    else:
        follow.delete()
        messages.info(request, f'Przestałeś obserwować wydarzenie "{event.title}".')

    return redirect('activities:event_detail', pk=pk)


from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.views.generic import CreateView
from django.urls import reverse

from communities.models import CommunityProfile, Membership
from .models import Announcement, Event, EventRole
from .forms import AnnouncementCreateForm
import django.db.models as models_db


class AnnouncementCreateView(LoginRequiredMixin, CreateView):
    """
    Formularz tworzenia ogłoszenia.

    Obsługuje trzy konteksty:
    - ?community=<pk> → ogłoszenie dla wspólnoty
    - ?event=<pk>     → ogłoszenie dla eventu
    - brak parametru  → użytkownik wybiera sam

    Po zapisaniu przekierowuje z powrotem do kontekstu (wspólnota/event/dashboard).
    """
    model = Announcement
    form_class = AnnouncementCreateForm
    template_name = 'activities/announcement_create.html'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()

        # Pobierz kontekst z parametrów URL
        self._community = None
        self._event = None

        community_pk = request.GET.get('community')
        event_pk = request.GET.get('event')

        if community_pk:
            self._community = get_object_or_404(CommunityProfile, pk=community_pk)
            # Sprawdź uprawnienia do wspólnoty
            has_permission = Membership.objects.filter(
                person=request.user,
                community=self._community,
                role__in=['owner', 'admin', 'leader', 'service_leader'],
                is_active=True,
            ).exists()
            if not has_permission:
                messages.error(request, 'Nie masz uprawnień do tworzenia ogłoszeń w tej wspólnocie.')
                return redirect('communities:community_detail', pk=community_pk)

        elif event_pk:
            self._event = get_object_or_404(Event, pk=event_pk)
            # Sprawdź uprawnienia do eventu
            my_communities = CommunityProfile.objects.filter(
                memberships__person=request.user,
                memberships__role__in=['owner', 'admin', 'leader', 'service_leader'],
                memberships__is_active=True,
            )
            has_permission = (
                EventRole.objects.filter(user=request.user, event=self._event).exists() or
                self._event.communities.filter(pk__in=my_communities).exists()
            )
            if not has_permission:
                messages.error(request, 'Nie masz uprawnień do tworzenia ogłoszeń dla tego wydarzenia.')
                return redirect('activities:event_detail', pk=event_pk)

        else:
            # Bez kontekstu - sprawdź czy ma uprawnienia gdziekolwiek
            can_create = Membership.objects.filter(
                person=request.user,
                role__in=['owner', 'admin', 'leader', 'service_leader'],
                is_active=True,
            ).exists()
            if not can_create:
                messages.error(request, 'Nie masz uprawnień do tworzenia ogłoszeń.')
                return redirect('communities:dashboard')

        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['community'] = self._community
        kwargs['event'] = self._event
        return kwargs

    def form_valid(self, form):
        announcement = form.save(commit=False)
        announcement.created_by = self.request.user
        announcement.save()

        messages.success(self.request, f'Ogłoszenie "{announcement.title}" zostało dodane.')
        return redirect(self._get_success_url(announcement))

    def _get_success_url(self, announcement):
        """Przekieruj z powrotem do kontekstu."""
        if announcement.community:
            return reverse('communities:community_detail', kwargs={'pk': announcement.community.pk})
        if announcement.event:
            return reverse('activities:event_detail', kwargs={'pk': announcement.event.pk})
        return reverse('communities:dashboard')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['community'] = self._community
        context['event'] = self._event
        return context