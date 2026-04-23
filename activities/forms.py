from django import forms
from django.utils import timezone
from django.db import models

from communities.models import CommunityProfile, Membership
from .models import Event, Announcement

class EventCreateForm(forms.ModelForm):
    """
    Formularz tworzenia wydarzenia.

    Pola wspólnot są filtrowane do tych, w których
    użytkownik ma rolę owner/admin/leader/service_leader.
    """

    # Główny organizator - wymagany
    owner_community = forms.ModelChoiceField(
        queryset=CommunityProfile.objects.none(),  # Wypełniane w __init__
        required=True,
        label='Główny organizator',
        help_text='Wspólnota odpowiedzialna za wydarzenie.',
        widget=forms.Select(attrs={'class': 'form-select'}),
    )

    # Współorganizatorzy - opcjonalni == ZOSTAWIAM NA RAZIE 🚩🚩
    co_organizers = forms.CharField(
        required=False,
        widget=forms.HiddenInput()
    ) # to przechowuje id wybranych wspólnot

    class Meta:
        model = Event
        fields = [
            'title',
            'description',
            'date_start',
            'date_end',
            'location',
            'is_public',
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa wydarzenia',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Opis wydarzenia...',
            }),
            'date_start': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'date_end': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
            }, format='%Y-%m-%dT%H:%M'),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Np. ul. Przykładowa 1, Kraków',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
        }
        labels = {
            'title': 'Nazwa wydarzenia',
            'description': 'Opis',
            'date_start': 'Data i godzina rozpoczęcia',
            'date_end': 'Data i godzina zakończenia (opcjonalne)',
            'location': 'Miejsce',
            'is_public': 'Wydarzenie publiczne',
        }
        help_texts = {
            'is_public': 'Publiczne wydarzenia są widoczne dla wszystkich. '
                         'Niepubliczne tylko dla członków wspólnoty.',
        }

    def __init__(self, *args, **kwargs):
        # Wyciągnij usera zanim wywołasz super().__init__
        self.user = kwargs.pop('user')
        super().__init__(*args, **kwargs)

        # Filtruj wspólnoty do tych gdzie user ma odpowiednią rolę
        my_communities = CommunityProfile.objects.filter(
            memberships__person=self.user,
            memberships__role__in=['owner', 'admin', 'leader', 'service_leader'],
            memberships__is_active=True,
        ).distinct()

        self.fields['owner_community'].queryset = my_communities

        # Format daty dla datetime-local input
        self.fields['date_start'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['date_end'].input_formats = ['%Y-%m-%dT%H:%M']

    def clean(self):
        cleaned_data = super().clean()
        date_start = cleaned_data.get('date_start')
        date_end = cleaned_data.get('date_end')

        if date_start and date_start < timezone.now():
            self.add_error('date_start', 'Data rozpoczęcia nie może być w przeszłości.')

        if date_start and date_end and date_end <= date_start:
            self.add_error('date_end', 'Data zakończenia musi być późniejsza niż data rozpoczęcia.')

        return cleaned_data
    
    #  DO ZMIANY ===== 🚩🚩🚩
    # def clean_co_organizers(self):
    #     data = self.cleaned_data.get('co_organizers')

    #     if not data:
    #         return []

    #     try:
    #         # ids = [int(x) for x in data.split(',') if x]
    #         ids = [int(x.strip()) for x in data.split(',') if x.strip()]
    #     except ValueError:
    #         raise forms.ValidationError("Nieprawidłowe dane wspólnot.")

    #     # 🔒 zabezpieczenie – czy wspólnoty istnieją
    #     valid_ids = CommunityProfile.objects.filter(
    #         id__in=ids,
    #         is_active=True).values_list('id', flat=True)

    #     return list(valid_ids)
    

class AnnouncementCreateForm(forms.ModelForm):
    """
    Formularz tworzenia ogłoszenia.

    Kontekstowy - zachowuje się inaczej zależnie od skąd go wywołano:
    - Ze strony wspólnoty → community pre-wypełnione, ukryte
    - Ze strony eventu   → event pre-wypełnione, ukryte
    - Samodzielnie       → użytkownik wybiera sam

    user jest wymagany w __init__ do filtrowania dostępnych wspólnot i eventów.
    """

    class Meta:
        model = Announcement
        fields = ['title', 'content', 'is_public', 'community', 'event']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Tytuł ogłoszenia',
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Treść ogłoszenia...',
            }),
            'is_public': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'community': forms.Select(attrs={
                'class': 'form-select',
            }),
            'event': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'title': 'Tytuł',
            'content': 'Treść',
            'is_public': 'Ogłoszenie publiczne',
            'community': 'Wspólnota',
            'event': 'Wydarzenie',
        }
        help_texts = {
            'is_public': 'Publiczne ogłoszenia widoczne dla wszystkich. '
                         'Niepubliczne tylko dla członków wspólnoty.',
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user')
        # Opcjonalne pre-wypełnienie kontekstu
        community = kwargs.pop('community', None)
        event = kwargs.pop('event', None)
        super().__init__(*args, **kwargs)

        # Filtruj wspólnoty - tylko te gdzie user ma uprawnienia
        my_communities = CommunityProfile.objects.filter(
            memberships__person=self.user,
            memberships__role__in=['owner', 'admin', 'leader', 'service_leader'],
            memberships__is_active=True,
        ).distinct()

        # Filtruj eventy - tylko te gdzie user ma uprawnienia
        # (rola przy evencie LUB rola w wspólnocie organizującej)
        from .models import Event
        my_events = Event.objects.filter(
            models.Q(roles__user=self.user) |
            models.Q(communities__in=my_communities)
        ).distinct()

        self.fields['community'].queryset = my_communities
        self.fields['community'].required = False
        self.fields['community'].empty_label = '— brak —'

        self.fields['event'].queryset = my_events
        self.fields['event'].required = False
        self.fields['event'].empty_label = '— brak —'

        # Pre-wypełnij i ukryj jeśli kontekst znany
        if community:
            self.fields['community'].initial = community
            self.fields['community'].widget = forms.HiddenInput()
            self.fields['event'].widget = forms.HiddenInput()

        elif event:
            self.fields['event'].initial = event
            self.fields['event'].widget = forms.HiddenInput()
            self.fields['community'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        community = cleaned_data.get('community')
        event = cleaned_data.get('event')

        if community and event:
            raise forms.ValidationError(
                'Ogłoszenie może dotyczyć wspólnoty LUB wydarzenia – nie obu naraz.'
            )
        if not community and not event:
            raise forms.ValidationError(
                'Wybierz wspólnotę lub wydarzenie dla tego ogłoszenia.'
            )
        return cleaned_data
    
