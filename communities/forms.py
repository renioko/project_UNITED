"""
Formularze dla aplikacji communities.

Zawiera formularze do:
- Tworzenia wspólnoty
- Edycji profilu wspólnoty
- Edycji profilu osoby (później)
"""

from django import forms
from .models import CommunityProfile, Tag


class CommunityCreateForm(forms.ModelForm):
    """
    Formularz tworzenia nowej wspólnoty.
    
    Używamy ModelForm - Django automatycznie generuje pola na podstawie modelu.
    Musimy tylko określić które pola pokazać i jak je stylować.
    
    WAŻNE: Pole 'created_by' NIE jest w formularzu - ustawiamy je automatycznie
    w widoku (current user).
    """
    
    class Meta:
        model = CommunityProfile
        fields = [
            'name',
            'description',
            'city',
            'parish',
            'denomination',
            'denomination_other',
            'tags',
            'contact_email',
            'contact_phone',
            'website',
            'photo_url',
            'logo_url',
        ]
        
        # Customizacja widgetów (HTML inputs)
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Pełna nazwa wspólnoty'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Krótki opis wspólnoty (max 500 znaków)...'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Np. Kraków'
            }),
            'parish': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa parafii (opcjonalne)'
            }),
            'denomination': forms.Select(attrs={
                'class': 'form-select'
            }),
            'denomination_other': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Podaj nazwę denominacji (jeśli wybrano "Inna")'
            }),
            'tags': forms.CheckboxSelectMultiple(),  # Checkboxy zamiast multi-select
            'contact_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'kontakt@wspolnota.pl'
            }),
            'contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '+48 123 456 789'
            }),
            'website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://nasza-wspolnota.pl'
            }),
            'photo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/zdjecie.jpg'
            }),
            'logo_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/logo.png'
            }),
        }
        
        # Customizacja labeli
        labels = {
            'name': 'Nazwa wspólnoty',
            'description': 'Krótki opis',
            'city': 'Miasto',
            'parish': 'Parafia',
            'denomination': 'Denominacja',
            'denomination_other': 'Inna denominacja',
            'tags': 'Tagi (charakter działalności)',
            'contact_email': 'Email kontaktowy',
            'contact_phone': 'Telefon kontaktowy',
            'website': 'Strona WWW',
            'photo_url': 'URL zdjęcia głównego',
            'logo_url': 'URL logo',
        }
        
        # Teksty pomocnicze
        help_texts = {
            'description': 'Krótki opis który pojawi się na liście wspólnot (max 500 znaków)',
            'tags': 'Zaznacz wszystkie pasujące tagi - pomaga innym znaleźć Waszą wspólnotę',
            'photo_url': 'Link do zdjęcia głównego wspólnoty (później dodamy upload)',
            'logo_url': 'Link do logo wspólnoty (opcjonalne)',
        }
    
    def __init__(self, *args, **kwargs):
        """
        Inicjalizacja formularza - tutaj możemy dodać dodatkową customizację.
        """
        super().__init__(*args, **kwargs)
        
        # Oznacz wymagane pola gwiazdką
        self.fields['name'].required = True
        self.fields['description'].required = True
        self.fields['city'].required = True
        
        # Reszta pól opcjonalna
        self.fields['parish'].required = False
        self.fields['denomination'].required = False
        self.fields['denomination_other'].required = False
        self.fields['tags'].required = False
        self.fields['contact_email'].required = False
        self.fields['contact_phone'].required = False
        self.fields['website'].required = False
        self.fields['photo_url'].required = False
        self.fields['logo_url'].required = False
    
    def clean(self):
        """
        Dodatkowa walidacja całego formularza.
        """
        cleaned_data = super().clean()
        
        # Jeśli wybrano denominację "Inna", pole denomination_other jest wymagane
        denomination = cleaned_data.get('denomination')
        denomination_other = cleaned_data.get('denomination_other')
        
        if denomination == 'other' and not denomination_other:
            self.add_error(
                'denomination_other',
                'Proszę podać nazwę denominacji jeśli wybrano "Inna".'
            )
        
        return cleaned_data


class CommunityEditForm(forms.ModelForm):
    """
    Formularz edycji wspólnoty - podobny do CreateForm ale z dodatkowymi polami.
    
    Może zawierać więcej pól niż formularz tworzenia (np. full_description, address).
    """
    
    class Meta:
        model = CommunityProfile
        fields = [
            'name',
            'description',
            'full_description',
            'city',
            'parish',
            'address',
            'denomination',
            'denomination_other',
            'tags',
            'contact_email',
            'contact_phone',
            'website',
            'photo_url',
            'logo_url',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'parish': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'denomination': forms.Select(attrs={'class': 'form-select'}),
            'denomination_other': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.CheckboxSelectMultiple(),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'photo_url': forms.URLInput(attrs={'class': 'form-control'}),
            'logo_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
        
        labels = {
            'full_description': 'Pełny opis działalności',
            'address': 'Adres (ulica, nr budynku)',
        }