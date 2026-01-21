from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Rozszerzony model użytkownika z typem konta
    # WAŻNE: Usunięto 'community' - wszyscy użytkownicy to osoby!
    # Wspólnoty nie są już użytkownikami.
    """
    USER_TYPE_CHOICES = (
        ('person', 'Osoba indywidualna'),
        # ('community', 'Wspólnota'),
    )
    
    # UWAGA: Zostawiamy pole user_type w modelu (dla kompatybilności wstecznej),
# ale domyślnie wszyscy są 'person' => 💡nie jest potrzebne, ale zostawie na przyszłośc, gdybym chciala dodac inne opcje
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='person',
        verbose_name='Typ użytkownika'
    )
    
    class Meta:
        verbose_name = 'Użytkownik'
        verbose_name_plural = 'Użytkownicy'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    # juz niepotrzebne - wszyscy uzytkownicy to 'osoby' - zostaje na przyszłośc, gdyby doszli inni rodzaje uzytkowników
    def is_person(self):
        """Sprawdź czy użytkownik to osoba."""
        return self.user_type == 'person'
    