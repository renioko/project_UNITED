from django.db import models
from django.conf import settings
from communities.models import CommunityProfile


# ===========================================================================
# EVENT
# ===========================================================================

class Event(models.Model):
    """
    Wydarzenie organizowane przez jedną lub wiele wspólnot.
    
    Relacja do wspólnot jest przez tabelę pośrednią EventCommunity,
    która określa rolę każdej wspólnoty (organizator główny / współorganizator).
    
    Koordynatorzy (osoby) są przypisani przez EventRole - niezależnie od
    ich roli w wspólnocie.
    
    Widoczność:
    - is_public=True  → widzi każdy
    - is_public=False → widzi tylko członek wspólnoty organizującej
    """

    communities = models.ManyToManyField(
        CommunityProfile,
        through='EventCommunity',
        related_name='events',
        verbose_name='Wspólnoty',
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Tytuł',
    )
    description = models.TextField(
        blank=True,
        verbose_name='Opis',
    )
    date_start = models.DateTimeField(
        verbose_name='Data rozpoczęcia',
    )
    date_end = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name='Data zakończenia',
    )
    location = models.CharField(
        max_length=300,
        blank=True,
        verbose_name='Miejsce',
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Publiczne',
        help_text='Publiczne wydarzenia są widoczne dla wszystkich użytkowników portalu.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_events',
        verbose_name='Utworzone przez',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['date_start']
        verbose_name = 'Wydarzenie'
        verbose_name_plural = 'Wydarzenia'

    def __str__(self):
        return self.title

    def get_owner_community(self):
        """Zwraca głównego organizatora (wspólnotę z rolą owner)."""
        try:
            return self.eventcommunity_set.get(role='owner').community
        except EventCommunity.DoesNotExist:
            return None

    def get_coordinators(self):
        """Zwraca wszystkich koordynatorów eventu."""
        return self.roles.filter(role='coordinator').select_related('user')

    def user_can_manage(self, user):
        """
        Czy użytkownik może zarządzać tym eventem?
        Może: owner eventu, koordynator eventu,
        oraz owner/admin/leader/service_leader wspólnoty organizującej.
        """
        if not user.is_authenticated:
            return False
        if user.is_superuser:
            return True

        # Rola przy evencie
        has_event_role = self.roles.filter(user=user).exists()
        if has_event_role:
            return True

        # Rola w wspólnocie organizującej
        organizing_communities = self.communities.all()
        has_community_role = CommunityProfile.objects.filter(
            pk__in=organizing_communities,
            memberships__person=user,
            memberships__role__in=['owner', 'admin', 'leader', 'service_leader'],
            memberships__is_active=True,
        ).exists()

        return has_community_role


class EventCommunity(models.Model):
    """
    Tabela pośrednia Event <-> CommunityProfile.

    Określa rolę każdej wspólnoty przy wydarzeniu:
    - owner        → organizator główny (jedna wspólnota, ma ostateczny głos)
    - co_organizer → współorganizator (może być wiele)
    """

    ROLE_CHOICES = [
        ('owner', 'Organizator główny'),
        ('co_organizer', 'Współorganizator'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        verbose_name='Wydarzenie',
    )
    community = models.ForeignKey(
        CommunityProfile,
        on_delete=models.CASCADE,
        verbose_name='Wspólnota',
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='co_organizer',
        verbose_name='Rola wspólnoty',
    )

    class Meta:
        unique_together = ('event', 'community')
        verbose_name = 'Wspólnota wydarzenia'
        verbose_name_plural = 'Wspólnoty wydarzenia'

    def __str__(self):
        return f"{self.community} – {self.event} ({self.get_role_display()})"


class EventRole(models.Model):
    """
    Rola użytkownika przy konkretnym evencie.
    Niezależna od roli w wspólnocie.

    Np. zwykły członek wspólnoty może być koordynatorem eventu.
    """

    ROLE_CHOICES = [
        ('owner', 'Owner eventu'),
        ('coordinator', 'Koordynator'),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name='Wydarzenie',
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_roles',
        verbose_name='Użytkownik',
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        verbose_name='Rola',
    )

    class Meta:
        unique_together = ('event', 'user')
        verbose_name = 'Rola w wydarzeniu'
        verbose_name_plural = 'Role w wydarzeniu'

    def __str__(self):
        return f"{self.user} – {self.event} ({self.get_role_display()})"


# ===========================================================================
# ANNOUNCEMENT
# ===========================================================================

class Announcement(models.Model):
    """
    Ogłoszenie dotyczące wspólnoty LUB wydarzenia.

    Zasada: dokładnie jedno FK jest ustawione (community XOR event).
    Pilnuje tego metoda clean().

    Widoczność:
    - is_public=True  → widzi każdy
    - is_public=False → widzi tylko członek danej wspólnoty
                        (obserwowanie nie daje dostępu do niepublicznych)

    Ogłoszenia eventu automatycznie "przebijają się" do wspólnot
    organizujących ten event - obsługuje to querysets.py.
    """

    community = models.ForeignKey(
        CommunityProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='announcements',
        verbose_name='Wspólnota',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='announcements',
        verbose_name='Wydarzenie',
    )

    title = models.CharField(
        max_length=200,
        verbose_name='Tytuł',
    )
    content = models.TextField(
        verbose_name='Treść',
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name='Publiczne',
        help_text='Niepubliczne ogłoszenia widoczne tylko dla członków wspólnoty.',
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='announcements',
        verbose_name='Autor',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Ogłoszenie'
        verbose_name_plural = 'Ogłoszenia'

    def __str__(self):
        return self.title

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.community and self.event:
            raise ValidationError(
                'Ogłoszenie może dotyczyć wspólnoty LUB wydarzenia – nie obu naraz.'
            )
        if not self.community and not self.event:
            raise ValidationError(
                'Ogłoszenie musi dotyczyć wspólnoty lub wydarzenia.'
            )

    @property
    def related_communities(self):
        """
        Wspólnoty powiązane z ogłoszeniem.
        - Dla ogłoszenia wspólnoty → ta wspólnota
        - Dla ogłoszenia eventu   → wszystkie wspólnoty organizujące event
        """
        if self.community:
            return CommunityProfile.objects.filter(pk=self.community.pk)
        if self.event:
            return self.event.communities.all()
        return CommunityProfile.objects.none()

    def is_visible_to(self, user):
        """
        Czy dany użytkownik może zobaczyć to ogłoszenie?
        Używaj w widoku szczegółu do sprawdzania uprawnień.
        """
        if self.is_public:
            return True

        # Niepubliczne - tylko członkowie wspólnoty
        related = self.related_communities
        return related.filter(
            memberships__person=user,
            memberships__is_active=True,
        ).exists()


# ===========================================================================
# FOLLOW
# ===========================================================================

class Follow(models.Model):
    """
    Obserwowanie wspólnoty lub wydarzenia przez użytkownika.

    Zasada: dokładnie jedno FK jest ustawione (community XOR event).
    Obserwowanie daje dostęp tylko do PUBLICZNYCH treści.
    Niepubliczne ogłoszenia wymagają członkostwa.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follows',
        verbose_name='Użytkownik',
    )
    community = models.ForeignKey(
        CommunityProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followers',
        verbose_name='Obserwowana wspólnota',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followers',
        verbose_name='Obserwowane wydarzenie',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'community'],
                condition=models.Q(community__isnull=False),
                name='unique_follow_community',
            ),
            models.UniqueConstraint(
                fields=['user', 'event'],
                condition=models.Q(event__isnull=False),
                name='unique_follow_event',
            ),
        ]
        verbose_name = 'Obserwowanie'
        verbose_name_plural = 'Obserwowania'

    def __str__(self):
        target = self.community or self.event
        return f"{self.user} obserwuje {target}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.community and self.event:
            raise ValidationError(
                'Można obserwować wspólnotę LUB wydarzenie – nie oba naraz.'
            )
        if not self.community and not self.event:
            raise ValidationError(
                'Musisz wybrać wspólnotę lub wydarzenie do obserwowania.'
            )