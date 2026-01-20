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
    Profil wspólnoty religijnej.
    
    WAŻNA ZMIANA ARCHITEKTONICZNA:
    Wspólnota NIE jest już użytkownikiem (User). To "grupa" zarządzana przez osoby.
    Osoby mają role (owner, admin, leader, member) przypisane przez Membership.
    
    Dzięki temu:
    - Wiele osób może zarządzać jedną wspólnotą
    - Łatwa zmiana liderów (zmiana roli, nie konta)
    - Jedna osoba może zarządzać wieloma wspólnotami
    - Bezpieczniejsze (każdy ma swoje konto, nie wspólne hasło)
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
    # === USUNIĘTE: user = OneToOneField ===
    # Wspólnota nie ma już bezpośredniej relacji do User!
    # Zamiast tego, relacja jest przez Membership (z rolami)
    
    # Podstawowe informacje (strona główna)
    )
    # user = models.OneToOneField(
    #     settings.AUTH_USER_MODEL,
    #     on_delete=models.CASCADE,
    #     limit_choices_to={'user_type': 'community'},
    #     related_name='community_profile',
    #     verbose_name='Użytkownik'
    # )
    
    # Podstawowe informacje (strona główna)
    name = models.CharField(max_length=200, verbose_name='Nazwa wspólnoty')
    # dodane slug
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name='Slug (URL)')
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
    # NOWE POLE - kto stworzył wspólnotę (dla historii) - zamiast user
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_communities',
        verbose_name='Utworzona przez',
        help_text='Osoba która założyła tę wspólnotę'
    )
    # founded_date = models.DateField(null=True, blank=True, verbose_name='Data założenia')
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
    
    # NOWE:  - dodanie funkcji save()
    def save(self, *args, **kwargs):
        """
        Auto-generuj slug z nazwy (dla ładnych URL-i).
        Np. "Wspólnota Emmanuel Kraków" → "wspolnota-emmanuel-krakow"
        """
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name, allow_unicode=True)
            slug = base_slug
            counter = 1
            
            # Upewnij się że slug jest unikalny
            while CommunityProfile.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)
    
    def get_member_count(self):
        """Zwraca liczbę członków"""
        return self.memberships.filter(is_active=True).count()
    
    # Nowe: - dodanie uprawnien
    def get_owners(self):
        """Zwraca listę właścicieli (owner) wspólnoty"""
        return self.memberships.filter(role='owner', is_active=True).select_related('person')
    
    def get_admins(self):
        """Zwraca listę administratorów (owner + admin) wspólnoty"""
        return self.memberships.filter(
            role__in=['owner', 'admin'], 
            is_active=True
        ).select_related('person')
    
    def user_can_edit(self, user):
        """
        Sprawdź czy dany użytkownik może edytować tę wspólnotę.
        Mogą: owner, admin
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        return self.memberships.filter(
            person=user,
            role__in=['owner', 'admin'],
            is_active=True
        ).exists()
    
    def user_can_manage_members(self, user):
        """
        Sprawdź czy użytkownik może zarządzać członkami (dodawać, usuwać, zmieniać role).
        Mogą: owner, admin, leader
        """
        if not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True
        
        return self.memberships.filter(
            person=user,
            role__in=['owner', 'admin', 'leader'],
            is_active=True
        ).exists()


class PersonProfile(models.Model):
    """
    Profil osoby indywidualnej - BEZ ZMIAN.
    
    Każdy użytkownik to osoba (user_type='person').
    Wspólnoty nie są już użytkownikami!
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
    Członkostwo osoby we wspólnocie - Z SYSTEMEM RÓL.
    
    HIERARCHIA RÓL (od najwyższej):
    1. OWNER - właściciel, pełne uprawnienia, może nadawać role
    2. ADMIN - administrator, może edytować profil i zarządzać członkami
    3. LEADER - lider, może zarządzać członkami
    4. SERVICE_LEADER - lider posługi/diakonii
    5. MEMBER - zwykły członek
    
    UPRAWNIENIA:
    - Edycja profilu wspólnoty: owner, admin
    - Zarządzanie członkami: owner, admin, leader
    - Tworzenie wydarzeń: owner, admin, leader, service_leader
    - Członkostwo: wszyscy
    """

    ROLE_CHOICES = (
        ('owner', 'Właściciel'),           # Założyciel/główny zarządca
        ('admin', 'Administrator'),         # Może wszystko poza nadawaniem owner
        ('leader', 'Lider'),               # Zarządza członkami i wydarzeniami
        ('service_leader', 'Lider diakonii'),  # Organizuje posługi
        ('member', 'Członek'),             # Zwykły członek
    )
    person = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'person'}, # TYLKO osoby mogą być członkami
        related_name='memberships',
        verbose_name='Członkowstwo'
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

    # NOWE POLA - dla lepszego zarządzania
    invited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invited_memberships',
        verbose_name='Zaproszony przez',
        help_text='Kto zaprosił tę osobę do wspólnoty'
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name='Notatki',
        help_text='Wewnętrzne notatki o członku (widoczne tylko dla adminów)'
    )
    class Meta:
        verbose_name = 'Członkostwo'
        verbose_name_plural = 'Członkostwa'
        unique_together = ('person', 'community')  # Osoba może należeć do wspólnoty tylko raz
        ordering = ['role','-joined_date'] # Sortuj: najpierw owners, potem admin, etc.
    
    def __str__(self):
        return f"{self.person.username} → {self.community.name} ({self.get_role_display()})"
    
    def is_owner(self):
        """Sprawdź czy to właściciel"""
        return self.role == 'owner'
    
    def is_admin_or_owner(self):
        """Sprawdź czy ma uprawnienia administracyjne"""
        return self.role in ['owner', 'admin']
    
    def can_manage_members(self):
        """Sprawdź czy może zarządzać członkami"""
        return self.role in ['owner', 'admin', 'leader']