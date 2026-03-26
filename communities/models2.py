from django.db import models
from django.conf import settings
from communities.models import CommunityProfile

# ===========================================================================
# EVENT
# ===========================================================================

class Event(models.Model):
    
    # Wspólnoty organizujące - wiele do wielu
    communities = models.ManyToManyField(
        CommunityProfile,
        through='EventCommunity',
        related_name='events',
        verbose_name='Wspólnoty',
    )
    
    title = models.CharField(max_length=200, verbose_name='Tytuł')
    description = models.TextField(blank=True, verbose_name='Opis')
    
    date_start = models.DateTimeField(verbose_name='Data rozpoczęcia')
    date_end = models.DateTimeField(blank=True, null=True, verbose_name='Data zakończenia')
    location = models.CharField(max_length=300, blank=True, verbose_name='Miejsce')
    
    is_public = models.BooleanField(default=True, verbose_name='Publiczne')
    
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


class EventCommunity(models.Model):
    """
    Tabela pośrednia Event <-> Community.
    Jedna wspólnota jest 'owner' eventu - ona ma ostateczną decyzję.
    Koordynatorzy są przypisani przez EventRole.
    """
    ROLE_CHOICES = [
        ('owner', 'Organizator główny'),
        ('co_organizer', 'Współorganizator'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    community = models.ForeignKey(CommunityProfile, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='co_organizer')

    class Meta:
        unique_together = ('event', 'community')
        verbose_name = 'Wspólnota wydarzenia'

    def __str__(self):
        return f"{self.community} – {self.event} ({self.role})"


class EventRole(models.Model):
    """
    Rola użytkownika przy konkretnym evencie.
    Niezależna od roli w wspólnocie.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('coordinator', 'Koordynator'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='roles')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='event_roles',
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    class Meta:
        unique_together = ('event', 'user')
        verbose_name = 'Rola w wydarzeniu'

    def __str__(self):
        return f"{self.user} – {self.event} ({self.role})"


# ===========================================================================
# ANNOUNCEMENT
# ===========================================================================

class Announcement(models.Model):
    """
    Ogłoszenie może dotyczyć wspólnoty LUB wydarzenia - nie obu naraz.
    Walidacja w clean() pilnuje że dokładnie jedno FK jest ustawione.
    """
    
    # Dokładnie jedno z tych dwóch powinno być ustawione
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

    title = models.CharField(max_length=200, verbose_name='Tytuł')
    content = models.TextField(verbose_name='Treść')
    is_public = models.BooleanField(default=True, verbose_name='Publiczne')

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
        Zwraca wspólnoty powiązane z ogłoszeniem.
        Dla ogłoszenia wspólnoty – ta wspólnota.
        Dla ogłoszenia eventu – wszystkie wspólnoty organizujące event.
        """
        if self.community:
            return CommunityProfile.objects.filter(pk=self.community.pk)
        if self.event:
            return self.event.communities.all()
        return CommunityProfile.objects.none()

    def is_visible_to(self, user):
        """
        Czy dany użytkownik może zobaczyć to ogłoszenie?
        Przydatne w widoku szczegółu.
        """
        if self.is_public:
            return True
        
        # Niepubliczne - sprawdź czy jest członkiem lub obserwuje
        related = self.related_communities
        is_member = related.filter(membership__person=user).exists()
        # is_following = related.filter(followers__user=user).exists()
        # return is_member or is_following
        return is_member
# ===========================================================================
# FOLLOW
# ===========================================================================

class Follow(models.Model):
    """
    Użytkownik może obserwować wspólnotę lub wydarzenie.
    Tak samo jak Announcement - dokładnie jedno FK ustawione.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='follows',
    )
    community = models.ForeignKey(
        CommunityProfile,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followers',
    )
    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='followers',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # Użytkownik może obserwować daną wspólnotę/event tylko raz
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

    def __str__(self):
        target = self.community or self.event
        return f"{self.user} obserwuje {target}"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.community and self.event:
            raise ValidationError('Można obserwować wspólnotę LUB wydarzenie – nie oba naraz.')
        if not self.community and not self.event:
            raise ValidationError('Musisz wybrać wspólnotę lub wydarzenie.')
        




# pozniej we views:
# # Ogłoszenia widoczne dla użytkownika
# def get_announcements_for_user(user):
#     my_communities = CommunityProfile.objects.filter(
#         membership__person=user
#     )
#     followed_communities = CommunityProfile.objects.filter(
#         followers__user=user
#     )
#     followed_events = Event.objects.filter(
#         followers__user=user
#     )

#     return Announcement.objects.filter(
#         # Moje wspólnoty - wszystkie ogłoszenia
#         models.Q(community__in=my_communities) |
#         models.Q(event__communities__in=my_communities) |
#         # Obserwowane - tylko publiczne
#         models.Q(community__in=followed_communities, is_public=True) |
#         models.Q(event__in=followed_events, is_public=True)
#     ).distinct()