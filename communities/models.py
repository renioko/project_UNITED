from django.db import models
from django.conf import settings
from django.core.validators import URLValidator

class Tag(models.Model):
    """
    Tagi do kategoryzacji wspólnot
    """
    name = models.CharField(max_length=50, unique=True, verbose_name='Nazwa tagu')
    slug = models.SlugField(max_length=50, unique=True)
    
    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tagi'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CommunityProfile(models.Model):
    """
    Profil wspólnoty religijnej
    """

    DENOMINATION_CHOICES = (
        ('catholic', 'Katolicka'),
        ('protestant', 'Protestancka'),
        ('orthodox', 'Prawosławna'),
        ('evangelical', 'Ewangelikalna'),
        ('pentecostal', 'Zielonoświątkowa'),
        ('baptist', 'Baptystyczna'),
        ('methodist', 'Metodystyczna'),
        ('charismatic', 'Charyzmatyczna'),
        ('other', 'Inna'),
    )
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'community'},
        related_name='community_profile',
        verbose_name='Użytkownik'
    )
    
    # Podstawowe informacje (strona główna)
    name = models.CharField(max_length=200, verbose_name='Nazwa wspólnoty')
    description = models.TextField(verbose_name='Krótki opis', max_length=500)
    city = models.CharField(max_length=100, verbose_name='Miasto')
    parish = models.CharField(max_length=200, blank=True, verbose_name='Parafia')

    # Denominacja
    denomination = models.CharField(
        max_length=50,
        choices=DENOMINATION_CHOICES,
        blank=True,
        verbose_name='Denominacja'
    )
    denomination_other = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='Inna denominacja (jeśli wybrano "Inna")',
        help_text='Wypełnij tylko jeśli wybrałeś "Inna"'
    )
    
    # Zdjęcia (na razie URL, później upload)
    photo_url = models.URLField(
        blank=True,
        validators=[URLValidator()],
        verbose_name='URL zdjęcia głównego'
    )
    logo_url = models.URLField(
        blank=True,
        validators=[URLValidator()],
        verbose_name='URL logo'
    )
    
    # Tagi
    tags = models.ManyToManyField(Tag, blank=True, related_name='communities', verbose_name='Tagi')
    
    # Dodatkowe informacje (podstrona "Informacje")
    full_description = models.TextField(blank=True, verbose_name='Pełny opis działalności')
    address = models.CharField(max_length=300, blank=True, verbose_name='Adres')
    contact_email = models.EmailField(blank=True, verbose_name='Email kontaktowy')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='Telefon')
    website = models.URLField(blank=True, verbose_name='Strona WWW')
    
    # Daty
    founded_date = models.DateField(null=True, blank=True, verbose_name='Data założenia')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia profilu')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ostatnia aktualizacja')
    
    # Status
    is_active = models.BooleanField(default=True, verbose_name='Profil aktywny')
    is_verified = models.BooleanField(default=False, verbose_name='Zweryfikowana')
    
    class Meta:
        verbose_name = 'Profil wspólnoty'
        verbose_name_plural = 'Profile wspólnot'
        ordering = ['-created_at']
    
    def __str__(self):
        return self.name
    
    def get_member_count(self):
        """Zwraca liczbę członków"""
        return self.memberships.filter(is_active=True).count()


class PersonProfile(models.Model):
    """
    Profil osoby indywidualnej
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'person'},
        related_name='person_profile',
        verbose_name='Użytkownik'
    )
    
    first_name = models.CharField(max_length=100, verbose_name='Imię')
    last_name = models.CharField(max_length=100, blank=True, verbose_name='Nazwisko')
    city = models.CharField(max_length=100, blank=True, verbose_name='Miasto')
    bio = models.TextField(max_length=500, blank=True, verbose_name='O mnie')
    
    # Zdjęcie profilowe (URL)
    photo_url = models.URLField(blank=True, verbose_name='URL zdjęcia')
    
    # Daty
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Data utworzenia')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Ostatnia aktualizacja')
    
    class Meta:
        verbose_name = 'Profil osoby'
        verbose_name_plural = 'Profile osób'
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}".strip() or self.user.username


class Membership(models.Model):
    """
    Członkostwo osoby we wspólnocie
    """
    ROLE_CHOICES = (
        ('member', 'Członek'),
        ('leader', 'Lider'),
        ('service_leader', 'Lider diakonii'),
        ('admin', 'Administrator'),
    )
    
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'person'},
        related_name='memberships',
        verbose_name='Osoba'
    )
    
    community = models.ForeignKey(
        CommunityProfile,
        on_delete=models.CASCADE,
        related_name='memberships',
        verbose_name='Wspólnota'
    )
    
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='member',
        verbose_name='Rola'
    )
    
    joined_date = models.DateTimeField(auto_now_add=True, verbose_name='Data dołączenia')
    is_active = models.BooleanField(default=True, verbose_name='Aktywne członkostwo')
    
    class Meta:
        verbose_name = 'Członkostwo'
        verbose_name_plural = 'Członkostwa'
        unique_together = ('person', 'community')  # Osoba może należeć do wspólnoty tylko raz
        ordering = ['-joined_date']
    
    def __str__(self):
        return f"{self.person.username} → {self.community.name} ({self.get_role_display()})"