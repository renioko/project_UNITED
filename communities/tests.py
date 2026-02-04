from django.test import TestCase
from django.contrib.auth import get_user_model
from django.db import IntegrityError
from communities.models import (
    Tag, 
    CommunityProfile, 
    PersonProfile, 
    Membership
)

User = get_user_model()


# ===== TESTY MODELU TAG =====

class TagModelTest(TestCase):
    """Testy modelu Tag"""
    
    def test_create_tag(self):
        """Test tworzenia tagu"""
        tag = Tag.objects.create(
            name='Modlitwa',
            slug='modlitwa'
        )
        
        self.assertEqual(tag.name, 'Modlitwa')
        self.assertEqual(str(tag), 'Modlitwa')
    
    def test_tag_slug_unique(self):
        """Test unikalności slug"""
        Tag.objects.create(name='Modlitwa', slug='modlitwa')
        
        with self.assertRaises(IntegrityError):
            Tag.objects.create(name='Modlitwa 2', slug='modlitwa')
    
    def test_tag_ordering(self):
        """Test sortowania tagów alfabetycznie"""
        Tag.objects.create(name='Charyzmat', slug='charyzmat')
        Tag.objects.create(name='Biblia', slug='biblia')
        Tag.objects.create(name='Adoracja', slug='adoracja')
        
        tags = list(Tag.objects.all())
        self.assertEqual(tags[0].name, 'Adoracja')
        self.assertEqual(tags[1].name, 'Biblia')
        self.assertEqual(tags[2].name, 'Charyzmat')


# ===== TESTY MODELU PERSON PROFILE =====

class PersonProfileModelTest(TestCase):
    """Testy modelu PersonProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='jankowalski',
            email='jan@example.com',
            password='Pass123!'
        )
    
    def test_create_person_profile(self):
        """Test tworzenia profilu osoby"""
        profile = PersonProfile.objects.create(
            user=self.user,
            first_name='Jan',
            last_name='Kowalski',
            city='Kraków'
        )
        
        self.assertEqual(profile.first_name, 'Jan')
        self.assertEqual(profile.user, self.user)
        self.assertEqual(str(profile), 'Jan Kowalski')
    
    def test_person_profile_str_without_last_name(self):
        """Test __str__ gdy brak nazwiska"""
        profile = PersonProfile.objects.create(
            user=self.user,
            first_name='Jan',
            last_name=''
        )
        
        self.assertEqual(str(profile), 'Jan')
    
    def test_person_profile_str_without_names(self):
        """Test __str__ gdy brak imienia i nazwiska"""
        profile = PersonProfile.objects.create(
            user=self.user,
            first_name='',
            last_name=''
        )
        
        self.assertEqual(str(profile), self.user.username)
    
    def test_one_profile_per_user(self):
        """Test że użytkownik może mieć tylko jeden profil"""
        PersonProfile.objects.create(
            user=self.user,
            first_name='Jan'
        )
        
        with self.assertRaises(IntegrityError):
            PersonProfile.objects.create(
                user=self.user,
                first_name='Anna'
            )


# ===== TESTY MODELU COMMUNITY PROFILE =====

class CommunityProfileModelTest(TestCase):
    """Testy modelu CommunityProfile"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='creator',
            email='creator@example.com',
            password='Pass123!'
        )
        
        self.person_profile = PersonProfile.objects.create(
            user=self.user,
            first_name='Jan'
        )
    
    def test_create_community(self):
        """Test tworzenia wspólnoty"""
        community = CommunityProfile.objects.create(
            name='Wspólnota Emmanuel',
            description='Wspólnota modlitwy',
            city='Kraków',
            created_by=self.user
        )
        
        self.assertEqual(community.name, 'Wspólnota Emmanuel')
        self.assertEqual(str(community), 'Wspólnota Emmanuel')
        self.assertTrue(community.is_active)
        self.assertFalse(community.is_verified)
    
    def test_auto_generate_slug(self):
        """Test automatycznego generowania slug"""
        community = CommunityProfile.objects.create(
            name='Wspólnota Emmanuel Kraków',
            description='Test',
            city='Kraków',
            created_by=self.user
        )
        
        self.assertEqual(community.slug, 'wspolnota-emmanuel-krakow')
    
    def test_slug_unique_increment(self):
        """Test że slug jest unikalny (dodaje -1, -2 etc)"""
        CommunityProfile.objects.create(
            name='Emmanuel',
            slug='emmanuel',
            description='Test',
            city='Kraków'
        )
        
        community2 = CommunityProfile.objects.create(
            name='Emmanuel',
            description='Test',
            city='Warszawa'
        )
        
        self.assertEqual(community2.slug, 'emmanuel-1')
    
    def test_get_member_count(self):
        """Test liczenia członków"""
        community = CommunityProfile.objects.create(
            name='Test Community',
            description='Test',
            city='Kraków'
        )
        
        # Dodaj 3 członków
        for i in range(3):
            user = User.objects.create_user(
                username=f'member{i}',
                email=f'member{i}@example.com',
                password='Pass123!'
            )
            Membership.objects.create(
                person=user,
                community=community,
                role='member'
            )
        
        self.assertEqual(community.get_member_count(), 3)
    
    def test_community_with_tags(self):
        """Test dodawania tagów do wspólnoty"""
        community = CommunityProfile.objects.create(
            name='Emmanuel',
            description='Test',
            city='Kraków'
        )
        
        tag1 = Tag.objects.create(name='Modlitwa', slug='modlitwa')
        tag2 = Tag.objects.create(name='Charyzmat', slug='charyzmat')
        
        community.tags.add(tag1, tag2)
        
        self.assertEqual(community.tags.count(), 2)
        self.assertIn(tag1, community.tags.all())


# ===== TESTY MODELU MEMBERSHIP =====

class MembershipModelTest(TestCase):
    """Testy modelu Membership (członkostwo)"""
    
    def setUp(self):
        # Utwórz użytkowników
        self.owner = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='Pass123!'
        )
        self.member = User.objects.create_user(
            username='member',
            email='member@example.com',
            password='Pass123!'
        )
        
        # Utwórz profile
        PersonProfile.objects.create(user=self.owner, first_name='Owner')
        PersonProfile.objects.create(user=self.member, first_name='Member')
        
        # Utwórz wspólnotę
        self.community = CommunityProfile.objects.create(
            name='Test Community',
            description='Test',
            city='Kraków',
            created_by=self.owner
        )
    
    def test_create_membership(self):
        """Test tworzenia członkostwa"""
        membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member'
        )
        
        self.assertEqual(membership.person, self.member)
        self.assertEqual(membership.community, self.community)
        self.assertEqual(membership.role, 'member')
        self.assertTrue(membership.is_active)
    
    def test_membership_str(self):
        """Test reprezentacji tekstowej członkostwa"""
        membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='admin'
        )
        
        expected = f"{self.member.username} → {self.community.name} (Administrator)"
        self.assertEqual(str(membership), expected)
    
    def test_unique_membership(self):
        """Test że osoba może być członkiem wspólnoty tylko raz"""
        Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member'
        )
        
        with self.assertRaises(IntegrityError):
            Membership.objects.create(
                person=self.member,
                community=self.community,
                role='admin'
            )
    
    def test_membership_roles(self):
        """Test różnych ról członkostwa"""
        roles = ['owner', 'admin', 'leader', 'service_leader', 'member']
        
        for i, role in enumerate(roles):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='Pass123!'
            )
            PersonProfile.objects.create(user=user, first_name=f'User{i}')
            
            membership = Membership.objects.create(
                person=user,
                community=self.community,
                role=role
            )
            
            self.assertEqual(membership.role, role)
    
    def test_is_owner_method(self):
        """Test metody is_owner()"""
        owner_membership = Membership.objects.create(
            person=self.owner,
            community=self.community,
            role='owner'
        )
        
        member_membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member'
        )
        
        self.assertTrue(owner_membership.is_owner())
        self.assertFalse(member_membership.is_owner())
    
    def test_is_admin_or_owner_method(self):
        """Test metody is_admin_or_owner()"""
        admin = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='Pass123!'
        )
        PersonProfile.objects.create(user=admin, first_name='Admin')
        
        owner_membership = Membership.objects.create(
            person=self.owner,
            community=self.community,
            role='owner'
        )
        
        admin_membership = Membership.objects.create(
            person=admin,
            community=self.community,
            role='admin'
        )
        
        member_membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member'
        )
        
        self.assertTrue(owner_membership.is_admin_or_owner())
        self.assertTrue(admin_membership.is_admin_or_owner())
        self.assertFalse(member_membership.is_admin_or_owner())
    
    def test_can_manage_members_method(self):
        """Test metody can_manage_members()"""
        leader = User.objects.create_user(
            username='leader',
            email='leader@example.com',
            password='Pass123!'
        )
        PersonProfile.objects.create(user=leader, first_name='Leader')
        
        owner_membership = Membership.objects.create(
            person=self.owner,
            community=self.community,
            role='owner'
        )
        
        leader_membership = Membership.objects.create(
            person=leader,
            community=self.community,
            role='leader'
        )
        
        member_membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member'
        )
        
        self.assertTrue(owner_membership.can_manage_members())
        self.assertTrue(leader_membership.can_manage_members())
        self.assertFalse(member_membership.can_manage_members())
    
    def test_invited_by_tracking(self):
        """Test śledzenia kto zaprosił członka"""
        membership = Membership.objects.create(
            person=self.member,
            community=self.community,
            role='member',
            invited_by=self.owner
        )
        
        self.assertEqual(membership.invited_by, self.owner)


# ===== TESTY UPRAWNIEŃ COMMUNITY =====

class CommunityPermissionsTest(TestCase):
    """Testy uprawnień do edycji wspólnoty"""
    
    def setUp(self):
        # Utwórz użytkowników z różnymi rolami
        self.owner = User.objects.create_user(
            username='owner', email='owner@example.com', password='Pass123!'
        )
        self.admin = User.objects.create_user(
            username='admin', email='admin@example.com', password='Pass123!'
        )
        self.leader = User.objects.create_user(
            username='leader', email='leader@example.com', password='Pass123!'
        )
        self.member = User.objects.create_user(
            username='member', email='member@example.com', password='Pass123!'
        )
        self.outsider = User.objects.create_user(
            username='outsider', email='outsider@example.com', password='Pass123!'
        )
        
        # Utwórz profile
        for user in [self.owner, self.admin, self.leader, self.member, self.outsider]:
            PersonProfile.objects.create(user=user, first_name=user.username)
        
        # Utwórz wspólnotę
        self.community = CommunityProfile.objects.create(
            name='Test Community',
            description='Test',
            city='Kraków',
            created_by=self.owner
        )
        
        # Dodaj członków z różnymi rolami
        Membership.objects.create(person=self.owner, community=self.community, role='owner')
        Membership.objects.create(person=self.admin, community=self.community, role='admin')
        Membership.objects.create(person=self.leader, community=self.community, role='leader')
        Membership.objects.create(person=self.member, community=self.community, role='member')
    
    def test_user_can_edit_permissions(self):
        """Test uprawnień do edycji wspólnoty"""
        # Owner i admin mogą edytować
        self.assertTrue(self.community.user_can_edit(self.owner))
        self.assertTrue(self.community.user_can_edit(self.admin))
        
        # Leader, member i outsider NIE mogą
        self.assertFalse(self.community.user_can_edit(self.leader))
        self.assertFalse(self.community.user_can_edit(self.member))
        self.assertFalse(self.community.user_can_edit(self.outsider))
    
    def test_user_can_manage_members_permissions(self):
        """Test uprawnień do zarządzania członkami"""
        # Owner, admin i leader mogą zarządzać
        self.assertTrue(self.community.user_can_manage_members(self.owner))
        self.assertTrue(self.community.user_can_manage_members(self.admin))
        self.assertTrue(self.community.user_can_manage_members(self.leader))
        
        # Member i outsider NIE mogą
        self.assertFalse(self.community.user_can_manage_members(self.member))
        self.assertFalse(self.community.user_can_manage_members(self.outsider))
    
    def test_superuser_permissions(self):
        """Test że superuser ma wszystkie uprawnienia"""
        superuser = User.objects.create_superuser(
            username='superuser',
            email='super@example.com',
            password='Pass123!'
        )
        
        self.assertTrue(self.community.user_can_edit(superuser))
        self.assertTrue(self.community.user_can_manage_members(superuser))
    
    def test_get_owners_method(self):
        """Test pobierania listy właścicieli"""
        owners = self.community.get_owners()
        
        self.assertEqual(owners.count(), 1)
        self.assertEqual(owners.first().person, self.owner)
    
    def test_get_admins_method(self):
        """Test pobierania listy adminów (owner + admin)"""
        admins = self.community.get_admins()
        
        self.assertEqual(admins.count(), 2)
        admin_users = [m.person for m in admins]
        self.assertIn(self.owner, admin_users)
        self.assertIn(self.admin, admin_users)