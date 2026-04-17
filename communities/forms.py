"""
Formularze dla aplikacji communities.

Zawiera formularze do:
- Tworzenia wspólnoty
- Edycji profilu wspólnoty
- Edycji profilu osoby (później)
"""

from django import forms
from .models import CommunityProfile, Tag
from .validators import validate_image_file
from cloudinary.models import CloudinaryResource

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
            'country',
            'parish',
            'latitude',
            'longitude',
            'denomination',
            'denomination_other',
            'tags',
            'contact_email',
            'contact_phone',
            'website',
            'photo',
            'logo',
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
                'country': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Np. Polska'
            }),
            'parish': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nazwa parafii (opcjonalne)'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '52.48018831646078', 
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder':'-1.8925135806710822',
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
            # Upload zdjęć - FileInput zamiast URLInput
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        
        # Customizacja labeli
        labels = {
            'name': 'Nazwa wspólnoty',
            'description': 'Krótki opis',
            'city': 'Miasto',
            'country': 'Państwo',
            'parish': 'Parafia',
            'latitude': 'Szerokość geograficzna',
            'longitude': 'Długość geograficzna',
            'denomination': 'Denominacja',
            'denomination_other': 'Inna denominacja',
            'tags': 'Tagi (charakter działalności)',
            'contact_email': 'Email kontaktowy',
            'contact_phone': 'Telefon kontaktowy',
            'website': 'Strona WWW',
            'photo': 'Zdjęcie',
            'logo': 'Logo',
        }
        
        # Teksty pomocnicze
        help_texts = {
            'latitude': 'Współrzędne geograficzne',
            'description': 'Krótki opis który pojawi się na liście wspólnot (max 500 znaków)',
            'tags': 'Zaznacz wszystkie pasujące tagi - pomaga innym znaleźć Waszą wspólnotę',
            'photo': 'Link do zdjęcia głównego wspólnoty (później dodamy upload)',
            'logo': 'Link do logo wspólnoty (opcjonalne)',
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
        self.fields['country'].required = True
        
        # Reszta pól opcjonalna
        self.fields['parish'].required = False
        self.fields['denomination'].required = False
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['denomination_other'].required = False
        self.fields['tags'].required = False
        self.fields['contact_email'].required = False
        self.fields['contact_phone'].required = False
        self.fields['website'].required = False
        self.fields['photo'].required = False
        self.fields['logo'].required = False
    
    def _validate_image_field(self, field_name):
        """
        Helper - waliduje pole obrazka tylko jeśli to świeży upload.
        CloudinaryResource = już na serwerze, pomijamy.
        """
        image = self.cleaned_data.get(field_name)
        if image and not isinstance(image, CloudinaryResource):
            validate_image_file(image)
        return image
    
    def clean_photo(self):
        return self._validate_image_field('photo')

    def clean_logo(self):
        return self._validate_image_field('logo')
    
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
            'country',
            'parish',
            'address',
            'latitude',
            'longitude',
            'denomination',
            'denomination_other',
            'tags',
            'contact_email',
            'contact_phone',
            'website',
            'photo',
            'logo',
        ]
        
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'full_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'parish': forms.TextInput(attrs={'class': 'form-control'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'denomination': forms.Select(attrs={'class': 'form-select'}),
            'denomination_other': forms.TextInput(attrs={'class': 'form-control'}),
            'tags': forms.CheckboxSelectMultiple(),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'website': forms.URLInput(attrs={'class': 'form-control'}),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'logo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
        }
        
        labels = {
            'full_description': 'Pełny opis działalności',
            'address': 'Adres (ulica, nr budynku)',
            'photo': 'Zdjęcie główne wspólnoty',  
            'logo': 'Logo wspólnoty',
        }

    def _validate_image_field(self, field_name):
        """
        Helper - waliduje pole obrazka tylko jeśli to świeży upload.
        CloudinaryResource = już na serwerze, pomijamy.
        """
        image = self.cleaned_data.get(field_name)
        if image and not isinstance(image, CloudinaryResource):
            validate_image_file(image)
        return image

    def clean_photo(self):
        return self._validate_image_field('photo')

    def clean_logo(self):
        return self._validate_image_field('logo')

    def clean(self):
        cleaned_data = super().clean()
        denomination = cleaned_data.get('denomination')
        denomination_other = cleaned_data.get('denomination_other')
        if denomination == 'other' and not denomination_other:
            self.add_error(
                'denomination_other',
                'Proszę podać nazwę denominacji jeśli wybrano "Inna".'
            )
        return cleaned_data