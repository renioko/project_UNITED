from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core import mail

User = get_user_model()


# ===== TESTY MODELI =====

class CustomUserModelTest(TestCase):
    """Testy modelu CustomUser"""
    
    def setUp(self):
        self.test_email = 'testuser@example.com'
        self.test_username = 'testuser'
        self.test_password = 'SecurePass123!'
    
    def test_create_user(self):
        """Test tworzenia zwykłego użytkownika"""
        user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        
        self.assertEqual(user.email, self.test_email)
        self.assertTrue(user.check_password(self.test_password))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
        # Sprawdź domyślny user_type
        self.assertEqual(user.user_type, 'person')
    
    def test_create_superuser(self):
        """Test tworzenia superusera"""
        admin = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password=self.test_password
        )
        
        self.assertTrue(admin.is_staff)
        self.assertTrue(admin.is_superuser)
    
    def test_user_string_representation(self):
        """Test reprezentacji tekstowej użytkownika"""
        user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        
        # __str__ zwraca "username (Typ użytkownika)"
        expected = f"{self.test_username} (Osoba indywidualna)"
        self.assertEqual(str(user), expected)
    
    def test_is_person_method(self):
        """Test metody is_person()"""
        user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        
        self.assertTrue(user.is_person())
    
    def test_default_user_type(self):
        """Test czy domyślny user_type to 'person'"""
        user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        
        self.assertEqual(user.user_type, 'person')


# ===== TESTY FORMULARZA =====

from accounts.forms import CustomSignupForm

class CustomSignupFormTest(TestCase):
    """Testy formularza rejestracji"""
    
    def test_form_valid_data(self):
        """Test formularza z poprawnymi danymi"""
        form = CustomSignupForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'Jan',
        })
        
        self.assertTrue(form.is_valid())
    
    def test_form_password_mismatch(self):
        """Test gdy hasła się nie zgadzają"""
        form = CustomSignupForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'DifferentPass123!',
            'first_name': 'Jan',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('Hasła nie są identyczne', str(form.errors))
    
    def test_form_password_too_short(self):
        """Test zbyt krótkiego hasła"""
        form = CustomSignupForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'short',
            'password2': 'short',
            'first_name': 'Jan',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('minimum 8 znaków', str(form.errors))
    
    def test_form_missing_first_name(self):
        """Test braku imienia"""
        form = CustomSignupForm({
            'username': 'testuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': '',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('first_name', form.errors)
    
    def test_form_duplicate_username(self):
        """Test duplikatu nazwy użytkownika"""
        # Utwórz użytkownika
        User.objects.create_user(
            username='testuser',
            email='existing@example.com',
            password='Pass123!'
        )
        
        # Spróbuj zarejestrować z tym samym username
        form = CustomSignupForm({
            'username': 'testuser',
            'email': 'new@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'Jan',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('username', form.errors)
    
    def test_form_duplicate_email(self):
        """Test duplikatu emaila"""
        # Utwórz użytkownika
        User.objects.create_user(
            username='existing',
            email='test@example.com',
            password='Pass123!'
        )
        
        # Spróbuj zarejestrować z tym samym emailem
        form = CustomSignupForm({
            'username': 'newuser',
            'email': 'test@example.com',
            'password1': 'SecurePass123!',
            'password2': 'SecurePass123!',
            'first_name': 'Jan',
        })
        
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)


# ===== TESTY AUTENTYKACJI =====

@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    ACCOUNT_EMAIL_VERIFICATION='mandatory'
)
class UserRegistrationTest(TestCase):
    """Testy rejestracji użytkownika"""
    
    def setUp(self):
        self.client = Client()
        self.signup_url = reverse('account_signup')
        self.test_email = 'testuser@example.com'
        self.test_username = 'testuser'
        self.test_password = 'SecurePass123!'
    
    def test_signup_page_loads(self):
        """Test czy strona rejestracji się ładuje"""
        response = self.client.get(self.signup_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Zarejestruj się')
    
    def test_user_registration_success(self):
        """Test pomyślnej rejestracji użytkownika"""
        response = self.client.post(self.signup_url, {
            'username': self.test_username,
            'email': self.test_email,
            'password1': self.test_password,
            'password2': self.test_password,
            'first_name': 'Jan',  # Wymagane!
        })
        
        # Sprawdź czy użytkownik został utworzony
        self.assertTrue(User.objects.filter(email=self.test_email).exists())
        
        # Sprawdź czy email weryfikacyjny został wysłany
        self.assertEqual(len(mail.outbox), 1)
        
        # Sprawdź czy użytkownik ma user_type='person'
        user = User.objects.get(email=self.test_email)
        self.assertEqual(user.user_type, 'person')
    
    def test_user_registration_password_mismatch(self):
        """Test rejestracji z różnymi hasłami"""
        response = self.client.post(self.signup_url, {
            'username': self.test_username,
            'email': self.test_email,
            'password1': self.test_password,
            'password2': 'DifferentPassword123!',
            'first_name': 'Jan',
        })
        
        # Użytkownik NIE powinien być utworzony
        self.assertFalse(User.objects.filter(email=self.test_email).exists())
        
        # Email NIE powinien być wysłany
        self.assertEqual(len(mail.outbox), 0)
    
    def test_user_registration_invalid_email(self):
        """Test rejestracji z nieprawidłowym emailem"""
        response = self.client.post(self.signup_url, {
            'username': self.test_username,
            'email': 'invalid-email',
            'password1': self.test_password,
            'password2': self.test_password,
            'first_name': 'Jan',
        })
        
        self.assertFalse(User.objects.filter(username=self.test_username).exists())
    
    def test_user_registration_missing_first_name(self):
        """Test rejestracji bez imienia"""
        response = self.client.post(self.signup_url, {
            'username': self.test_username,
            'email': self.test_email,
            'password1': self.test_password,
            'password2': self.test_password,
            'first_name': '',  # Puste
        })
        
        # Nie powinno się udać
        self.assertFalse(User.objects.filter(email=self.test_email).exists())


class UserLoginTest(TestCase):
    """Testy logowania użytkownika"""
    
    def setUp(self):
        self.client = Client()
        self.login_url = reverse('account_login')
        self.test_email = 'testuser@example.com'
        self.test_username = 'testuser'
        self.test_password = 'SecurePass123!'
        
        # Utwórz użytkownika
        self.user = User.objects.create_user(
            username=self.test_username,
            email=self.test_email,
            password=self.test_password
        )
        # Utwórz PersonProfile (wymagany przez Twoją aplikację)
        from communities.models import PersonProfile
        PersonProfile.objects.create(
            user=self.user,
            first_name='Jan'
        )
        # WAŻNE: Oznacz email jako zweryfikowany
        from allauth.account.models import EmailAddress
        EmailAddress.objects.create(
            user=self.user,
            email=self.test_email,
            verified=True,
            primary=True
        )
    
    def test_login_page_loads(self):
        """Test czy strona logowania się ładuje"""
        response = self.client.get(self.login_url)
        self.assertEqual(response.status_code, 200)
    
    def test_user_login_with_email_success(self):
        """Test pomyślnego logowania emailem"""
        response = self.client.post(self.login_url, {
            'login': self.test_email,
            'password': self.test_password,
        }, follow=True)
        
        # Sprawdź czy użytkownik jest zalogowany
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, self.test_username)
    
    def test_user_login_with_username_success(self):
        """Test pomyślnego logowania username"""
        response = self.client.post(self.login_url, {
            'login': self.test_username,
            'password': self.test_password,
        }, follow=True)
        
        # Sprawdź czy użytkownik jest zalogowany
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, self.test_username)
    
    def test_user_login_wrong_password(self):
        """Test logowania z błędnym hasłem"""
        response = self.client.post(self.login_url, {
            'login': self.test_email,
            'password': 'WrongPassword123!',
        })
        
        # Użytkownik NIE powinien być zalogowany
        # Strona powinna wyświetlić błąd (nie przekierować)
        self.assertEqual(response.status_code, 200)
        # Sprawdź czy jest komunikat o błędzie
        self.assertContains(response, 'email')
    
    def test_user_logout(self):
        """Test wylogowania"""
        # Najpierw zaloguj
        self.client.login(username=self.test_username, password=self.test_password)
        
        # Wyloguj
        logout_url = reverse('account_logout')
        response = self.client.post(logout_url)
        
        # Sprawdź przekierowanie
        self.assertEqual(response.status_code, 302)


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class EmailVerificationTest(TestCase):
    """Testy weryfikacji emaila"""
    
    def setUp(self):
        self.client = Client()
        self.test_email = 'testuser@example.com'
        self.test_username = 'testuser'
        self.test_password = 'SecurePass123!'
    
    def test_email_verification_sent(self):
        """Test czy email weryfikacyjny jest wysyłany"""
        signup_url = reverse('account_signup')
        self.client.post(signup_url, {
            'username': self.test_username,
            'email': self.test_email,
            'password1': self.test_password,
            'password2': self.test_password,
            'first_name': 'Jan',
        })
        
        # Sprawdź czy email został wysłany
        self.assertEqual(len(mail.outbox), 1)
        
        # Sprawdź treść emaila
        email = mail.outbox[0]
        self.assertIn(self.test_email, email.to)
        
        # Sprawdź czy email zawiera link weryfikacyjny
        self.assertIn('http', email.body)