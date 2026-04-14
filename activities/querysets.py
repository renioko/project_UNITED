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

# ===============================
from django.db.models import Q
from communities.models import CommunityProfile
from .models import Announcement, Event


def get_announcements_for_user(user):
    """
    Zwraca ogłoszenia widoczne dla danego użytkownika.

    Zasady widoczności:
    1. Publiczne → widzi każdy (zalogowany i niezalogowany)
    2. Niepubliczne → tylko członkowie wspólnoty (obserwowanie nie wystarczy)

    Ogłoszenia eventu "przebijają się" do wspólnot organizujących -
    członek wspólnoty widzi niepubliczne ogłoszenia eventów swojej wspólnoty.
    """

    if not user.is_authenticated:
        # Niezalogowany widzi tylko publiczne
        return Announcement.objects.filter(is_public=True)

    # Wspólnoty których użytkownik jest aktywnym członkiem
    my_communities = CommunityProfile.objects.filter(
        memberships__person=user,
        memberships__is_active=True,
    )

    # Wspólnoty które użytkownik obserwuje
    followed_communities = CommunityProfile.objects.filter(
        followers__user=user,
    )

    # Eventy które użytkownik obserwuje
    followed_events = Event.objects.filter(
        followers__user=user,
    )

    return Announcement.objects.filter(
        # Ogłoszenia mojej wspólnoty - publiczne i niepubliczne
        Q(community__in=my_communities) |

        # Ogłoszenia eventu mojej wspólnoty - publiczne i niepubliczne
        Q(event__communities__in=my_communities) |

        # Ogłoszenia obserwowanych wspólnot - tylko publiczne
        Q(community__in=followed_communities, is_public=True) |

        # Ogłoszenia obserwowanych eventów - tylko publiczne
        Q(event__in=followed_events, is_public=True)

    ).distinct()


def get_events_for_user(user):
    """
    Zwraca wydarzenia widoczne dla danego użytkownika.

    Zasady widoczności:
    1. Publiczne → widzi każdy
    2. Niepubliczne → tylko członkowie wspólnoty organizującej
                    lub osoby z rolą przy evencie
    """

    if not user.is_authenticated:
        return Event.objects.filter(is_public=True)

    my_communities = CommunityProfile.objects.filter(
        memberships__person=user,
        memberships__is_active=True,
    )

    followed_events = Event.objects.filter(
        followers__user=user,
    )

    # Eventy gdzie użytkownik ma rolę (koordynator, owner eventu)
    my_event_roles = Event.objects.filter(
        roles__user=user,
    )

    return Event.objects.filter(
        # Publiczne - widzi każdy
        Q(is_public=True) |

        # Niepubliczne mojej wspólnoty
        Q(is_public=False, communities__in=my_communities) |

        # Niepubliczne gdzie mam rolę przy evencie
        Q(is_public=False, pk__in=my_event_roles) |

        # Obserwowane publiczne (już objęte przez is_public=True,
        # ale zostawiamy dla jasności logiki)
        Q(pk__in=followed_events, is_public=True)

    ).distinct()