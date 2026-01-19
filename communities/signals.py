"""
Sygnały Django dla aplikacji communities.

Sygnały to automatyczne akcje wywoływane po określonych wydarzeniach,
np. po zapisaniu obiektu do bazy danych.

Używamy ich do automatycznego tworzenia członkostwa (Membership)
gdy ktoś zakłada nową wspólnotę.
"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CommunityProfile, Membership


@receiver(post_save, sender=CommunityProfile)
def create_owner_membership(sender, instance, created, **kwargs):
    """
    Automatycznie dodaj założyciela wspólnoty jako właściciela (owner).
    
    Parametry:
        sender - model który wysłał sygnał (CommunityProfile)
        instance - konkretny obiekt który został zapisany
        created - True jeśli to nowy obiekt, False jeśli aktualizacja
        **kwargs - dodatkowe argumenty
    
    Logika:
        - Jeśli to NOWA wspólnota (created=True)
        - I ma przypisanego założyciela (created_by)
        - I założyciel jeszcze NIE jest członkiem
        - To stwórz Membership z rolą 'owner'
    """
    
    # Tylko dla nowo utworzonych wspólnot
    if not created:
        return
    
    # Sprawdź czy wspólnota ma założyciela
    if not instance.created_by:
        return
    
    # Sprawdź czy założyciel już jest członkiem (może został dodany ręcznie) =//na pewno nie//
    membership_exists = Membership.objects.filter(
        person=instance.created_by,
        community=instance
    ).exists()
    
    if membership_exists:
        # Już jest członkiem, nie dodawaj ponownie
        return
    
    # Stwórz członkostwo z rolą OWNER
    Membership.objects.create(
        person=instance.created_by,
        community=instance,
        role='owner',
        is_active=True,
        # invited_by można zostawić puste (sam się dodał jako założyciel)
    )
    
    print(f"✅ Automatycznie dodano {instance.created_by.username} jako owner wspólnoty '{instance.name}'")