from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    """
    Rozszerzony model użytkownika z typem konta
    """
    USER_TYPE_CHOICES = (
        ('person', 'Osoba indywidualna'),
        ('community', 'Wspólnota'),
    )
    
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
    
    def is_community(self):
        return self.user_type == 'community'
    
    def is_person(self):
        return self.user_type == 'person'