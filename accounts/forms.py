# from django import forms
# # from allauth.account.forms import SignupForm
# from allauth.account.forms import BaseSignupForm
# from .models import CustomUser

# # class CustomSignupForm(SignupForm):
# class CustomSignupForm(BaseSignupForm):
#     """
#     Rozszerzony formularz rejestracji django-allauth.
#     Dodajemy pole wyboru typu użytkownika (Osoba/Wspólnota).
    
#     Django-allauth automatycznie używa tego formularza jeśli
#     ustawimy ACCOUNT_SIGNUP_FORM_CLASS w settings.py
#     """
    
#     # Pole wyboru typu użytkownika
#     user_type = forms.ChoiceField(
#         choices=CustomUser.USER_TYPE_CHOICES,
#         label='Typ konta',
#         widget=forms.RadioSelect,  # Radio buttons zamiast dropdown
#         initial='person',  # Domyślnie zaznaczona "Osoba"
#         help_text='Wybierz czy rejestrujesz się jako osoba indywidualna czy jako wspólnota.'
#     )

#     # Dodatkowe pola dla OSOBY
#     first_name = forms.CharField(
#         max_length=100,
#         required=False,  # Nie wymagane na start (user może wypełnić później)
#         label='Imię',
#         widget=forms.TextInput(attrs={'placeholder': 'Twoje imię'})
#     )
    
#     # Dodatkowe pola dla WSPÓLNOTY
#     community_name = forms.CharField(
#         max_length=200,
#         required=False,  # Nie wymagane na start
#         label='Nazwa wspólnoty',
#         widget=forms.TextInput(attrs={'placeholder': 'Pełna nazwa Twojej wspólnoty'})
#     )

#     def __init__(self, *args, **kwargs):
#         """
#         Metoda inicjalizacji - wywoływana gdy formularz jest tworzony.
#         Możemy tu customizować wygląd pól.
#         """
#         super().__init__(*args, **kwargs)
        
#         # Customizacja istniejących pól allauth
#         self.fields['username'].widget.attrs.update({
#             'class': 'form-control',
#             'placeholder': 'Wybierz nazwę użytkownika'
#         })
#         self.fields['email'].widget.attrs.update({
#             'class': 'form-control',
#             'placeholder': 'twoj-email@example.com'
#         })
#         self.fields['password1'].widget.attrs.update({
#             'class': 'form-control',
#             'placeholder': 'Minimum 8 znaków'
#         })
#         self.fields['password2'].widget.attrs.update({
#             'class': 'form-control',
#             'placeholder': 'Powtórz hasło'
#         })
        
                
#         # Dodaj klasy Bootstrap do nowych pól
#         self.fields['first_name'].widget.attrs.update({'class': 'form-control'})
#         self.fields['community_name'].widget.attrs.update({'class': 'form-control'})
    
#     def clean(self):
#         """
#         Walidacja formularza - sprawdzamy czy wypełnione poprawnie.
#         Wywoływane automatycznie przez Django przed zapisaniem.
#         """
#         cleaned_data = super().clean()
#         user_type = cleaned_data.get('user_type')
#         first_name = cleaned_data.get('first_name')
#         community_name = cleaned_data.get('community_name')
        
#         # Jeśli ktoś wybiera "Osoba", powinien podać imię
#         if user_type == 'person' and not first_name:
#             self.add_error('first_name', 'Proszę podać imię.')
        
#         # Jeśli ktoś wybiera "Wspólnota", powinien podać nazwę wspólnoty
#         if user_type == 'community' and not community_name:
#             self.add_error('community_name', 'Proszę podać nazwę wspólnoty.')
        
#         return cleaned_data
    
        
#     def save(self, request):
#         """
#         Zapisywanie użytkownika - wywoływane po pomyślnej walidacji.
#         Tu ustawiamy user_type i tworzymy odpowiedni profil.
#         """
#         # Najpierw wywołać standardowe zapisywanie allauth (tworzy CustomUser)
#         user = super().save(request)
        
#         # Pobierz dane z formularza
#         user_type = self.cleaned_data['user_type']
        
#         # Ustaw typ użytkownika
#         user.user_type = user_type
#         user.save()
        
#         # Stwórz odpowiedni profil w zależności od typu
#         if user_type == 'person':
#             from communities.models import PersonProfile
#             PersonProfile.objects.create(
#                 user=user,
#                 first_name=self.cleaned_data.get('first_name', '')
#             )
        
#         elif user_type == 'community':
#             from communities.models import CommunityProfile
#             CommunityProfile.objects.create(
#                 user=user,
#                 name=self.cleaned_data.get('community_name', user.username),
#                 # Pola wymagane w modelu - ustaw domyślne wartości
#                 description='',  # Pusty na razie, user wypełni w profilu
#                 city='',  # Do wypełnienia później
#             )
        
#         # Zwróć użytkownika (allauth potrzebuje tego)
#         return user
    

# ## **Dlaczego to działa?**
# ### **Problem był:**
# # allauth.account.forms → próbuje załadować accounts.forms (nasz custom)
# #     → accounts.forms importuje SignupForm z allauth.account.forms
# #         → allauth.account.forms jeszcze się nie załadował!
# #             → CIRCULAR IMPORT ERROR

"""
Formularze rejestracji dla Portal UNITED.

Ten plik definiuje custom formularz rejestracji dla django-allauth,
który obsługuje dwa typy użytkowników: Osoby i Wspólnoty.

WAŻNE: NIE importujemy nic z allauth.account.forms, żeby uniknąć circular import!
Zamiast tego definiujemy wszystkie pola ręcznie.
"""

from django import forms
from django.contrib.auth import get_user_model

# Pobierz model użytkownika (CustomUser)
User = get_user_model()


class CustomSignupForm(forms.Form):
    """
    Formularz rejestracji z wyborem typu użytkownika.
    
    Django-allauth automatycznie używa tego formularza gdy ustawimy:
    ACCOUNT_SIGNUP_FORM_CLASS = 'accounts.forms.CustomSignupForm'
    
    Musimy zdefiniować wszystkie pola ręcznie (username, email, password)
    ponieważ nie możemy dziedziczyć z BaseSignupForm (circular import).
    """
    
    # ========================================================================
    # POLA STANDARDOWE (wymagane przez allauth)
    # ========================================================================
    
    username = forms.CharField(
        max_length=150,
        label='Nazwa użytkownika',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Wybierz nazwę użytkownika',
            'autocomplete': 'username'
        })
    )
    
    email = forms.EmailField(
        label='Adres email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'twoj-email@example.com',
            'autocomplete': 'email'
        })
    )
    
    password1 = forms.CharField(
        label='Hasło',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Minimum 8 znaków',
            'autocomplete': 'new-password'
        })
    )
    
    password2 = forms.CharField(
        label='Powtórz hasło',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Powtórz hasło',
            'autocomplete': 'new-password'
        })
    )
    
    # ========================================================================
    # POLA CUSTOM - specyficzne dla naszej aplikacji
    # ========================================================================
    
    user_type = forms.ChoiceField(
        choices=[
            ('person', 'Osoba indywidualna'),
            ('community', 'Wspólnota')
        ],
        label='Typ konta',
        widget=forms.RadioSelect,
        initial='person',
        help_text='Wybierz czy rejestrujesz się jako osoba czy jako wspólnota.'
    )
    
    # Pole dla osób
    first_name = forms.CharField(
        max_length=100,
        required=False,
        label='Imię',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Twoje imię'
        })
    )
    
    # Pole dla wspólnot
    community_name = forms.CharField(
        max_length=200,
        required=False,
        label='Nazwa wspólnoty',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Pełna nazwa Twojej wspólnoty'
        })
    )
    
    # ========================================================================
    # WALIDACJA FORMULARZA
    # ========================================================================
    
    def clean_username(self):
        """
        Sprawdź czy nazwa użytkownika jest unikalna.
        Django wywołuje tę metodę automatycznie dla pola 'username'.
        """
        username = self.cleaned_data.get('username')
        
        # Sprawdź czy użytkownik o tej nazwie już istnieje
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('Ta nazwa użytkownika jest już zajęta.')
        
        return username
    
    def clean_email(self):
        """
        Sprawdź czy email jest unikalny.
        """
        email = self.cleaned_data.get('email')
        
        # Sprawdź czy email jest już w bazie
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Ten adres email jest już zarejestrowany.')
        
        return email
    
    def clean(self):
        """
        Walidacja całego formularza - sprawdź hasła i wymagane pola.
        Wywoływane po walidacji pojedynczych pól.
        """
        cleaned_data = super().clean()
        
        # Sprawdź czy hasła się zgadzają
        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')
        
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError('Hasła nie są identyczne.')
            
            # Sprawdź minimalną długość (allauth sprawdzi bardziej zaawansowane reguły)
            if len(password1) < 8:
                raise forms.ValidationError('Hasło musi mieć minimum 8 znaków.')
        
        # Sprawdź czy wypełniono odpowiednie pole w zależności od typu
        user_type = cleaned_data.get('user_type')
        first_name = cleaned_data.get('first_name')
        community_name = cleaned_data.get('community_name')
        
        if user_type == 'person' and not first_name:
            self.add_error('first_name', 'Proszę podać imię.')
        
        if user_type == 'community' and not community_name:
            self.add_error('community_name', 'Proszę podać nazwę wspólnoty.')
        
        return cleaned_data
    
    # ========================================================================
    # ZAPISYWANIE UŻYTKOWNIKA
    # ========================================================================
    
    def signup(self, request, user):
        """
        Metoda wywoływana przez allauth po stworzeniu użytkownika.
        
        Parametry:
            request - obiekt HTTP request
            user - już stworzony obiekt CustomUser (ale bez user_type i profilu)
        
        Tu ustawiamy user_type i tworzymy odpowiedni profil.
        """
        # Pobierz dane z formularza
        user_type = self.cleaned_data['user_type']
        
        # Ustaw typ użytkownika
        user.user_type = user_type
        user.save()
        
        # Stwórz odpowiedni profil
        if user_type == 'person':
            # Import tu (nie na górze) żeby uniknąć circular imports
            from communities.models import PersonProfile
            
            PersonProfile.objects.create(
                user=user,
                first_name=self.cleaned_data.get('first_name', '')
            )
        
        elif user_type == 'community':
            # Import tu (nie na górze) żeby uniknąć circular imports
            from communities.models import CommunityProfile
            
            CommunityProfile.objects.create(
                user=user,
                name=self.cleaned_data.get('community_name', user.username),
                description='Opis do uzupełnienia',  # Placeholder
                city='Do uzupełnienia',  # User wypełni później w profilu
            )
        
        # Nie trzeba return - allauth już ma obiekt user