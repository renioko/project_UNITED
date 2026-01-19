from django.contrib import admin
from .models import Tag, CommunityProfile, PersonProfile, Membership
from accounts.models import CustomUser
# from allauth.account.models import EmailAddress

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(CommunityProfile)
class CommunityProfileAdmin(admin.ModelAdmin):
    """
    Panel administracyjny dla profili wspólnot.
    
    WAŻNE ZMIANY:
    - Usunięto pole 'user' (wspólnota nie jest już użytkownikiem)
    - Dodano pole 'created_by' (kto założył wspólnotę)
    - Dodano pole 'slug' (dla ładnych URL)
    """
    list_display = [
        'name', 
        'city', 
        'denomination', 
        'parish', 
        'member_count', 
        'is_active', 
        'is_verified', 
        'created_at'
        ]
    list_filter = [
        'is_active', 
        'is_verified', 
        'denomination', 
        'city', 
        'tags',
        ]
    search_fields = ['name', 'city', 'parish', 'description']
    filter_horizontal = ['tags']  # Ładny interfejs do wyboru tagów
    readonly_fields = [
        'created_at', 
        'updated_at',
        'get_member_count',
        ]

    prepopulated_fields = {'slug': ('name',)}

    fieldsets = (
        ('Podstawowe informacje', {
            'fields': (
                'name',
                'slug',
                'description', 
                'city', 
                'parish',
                'created_by',  # ← ZMIENIONE: było 'user', teraz 'created_by'
            )
        }),
        ('Denominacja', {
            'fields': ('denomination', 'denomination_other')
        }),
        ('Zdjęcia', {
            'fields': ('photo_url', 'logo_url'),
            'classes': ('collapse',)  # Domyślnie zwinięte
        }),
        ('Dodatkowe informacje', {
            'fields': (
                'full_description', 
                'address', 
                'contact_email', 
                'contact_phone', 
                'website', 
                # 'founded_date'
                ),
            'classes': ('collapse',)
        }),
        ('Tagi', {
            'fields': ('tags',)
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified', 'created_at', 'updated_at')
        }),
    )
    def member_count(self, obj):
        return obj.get_member_count()
    member_count.short_description = 'Liczba członków'

@admin.register(PersonProfile)
class PersonProfileAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name', 'city', 'user', 'created_at']
    search_fields = ['first_name', 'last_name', 'city', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informacje osobiste', {
            'fields': ('user', 'first_name', 'last_name', 'city')
        }),
        ('O mnie', {
            'fields': ('bio', 'photo_url')
        }),
        ('Daty', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    """
    Panel administracyjny dla członkostwa.
    
    ZMIANY:
    - Dodano nowe role (owner, admin)
    - Dodano pola: invited_by, notes
    """

    list_display = [
        'person', 
        'community', 
        'role', 
        'joined_date', 
        'is_active',
        'invited_by',  # ← NOWE
        ]
    list_filter = ['role', 'is_active', 'joined_date']

    search_fields = [
        'person__username', 
        'person__person_profile__first_name',
        'person__person_profile__last_name',
        'community__name'
    ]
    readonly_fields = ['joined_date']
    
    fieldsets = (
        ('Członkostwo', {
            'fields': ('person', 'community', 'role', 'is_active')
        }),
        ('Dodatkowe', {
            'fields': ('invited_by', 'notes'),
            'classes': ('collapse',)
        }),
        ('Informacje', {
            'fields': ('joined_date',)
        }),
    )
    
    # Pokazuj tylko osoby (user_type='person') przy wyborze
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        Customizacja pól ForeignKey w formularzu admina.
        - 'person' i 'invited_by' - tylko użytkownicy typu 'person'
        """
        if db_field.name in ['person', 'invited_by']:
        # if db_field.name == "person":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='person')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


# # Lepsze wyświetlanie emaili w adminie
# @admin.register(EmailAddress)
# class EmailAddressAdmin(admin.ModelAdmin):
#     list_display = ['email', 'user', 'verified', 'primary']
#     list_filter = ['verified', 'primary']
#     search_fields = ['email', 'user__username']
#     readonly_fields = ['user']