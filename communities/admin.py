from django.contrib import admin
from .models import Tag, CommunityProfile, PersonProfile, Membership
from accounts.models import CustomUser

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name']

@admin.register(CommunityProfile)
class CommunityProfileAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'denomination', 'parish', 'member_count', 'is_active', 'is_verified', 'created_at']
    list_filter = ['is_active', 'is_verified', 'denomination', 'city', 'tags']
    search_fields = ['name', 'city', 'parish']
    filter_horizontal = ['tags']  # Ładny interfejs do wyboru tagów
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('user', 'name', 'description', 'city', 'parish')
        }),
        ('Denominacja', {
            'fields': ('denomination', 'denomination_other')
        }),
        ('Zdjęcia', {
            'fields': ('photo_url', 'logo_url'),
            'classes': ('collapse',)  # Domyślnie zwinięte
        }),
        ('Dodatkowe informacje', {
            'fields': ('full_description', 'address', 'contact_email', 'contact_phone', 'website', 'founded_date'),
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
    list_display = ['person', 'community', 'role', 'joined_date', 'is_active']
    list_filter = ['role', 'is_active', 'joined_date']
    search_fields = ['person__username', 'community__name']
    readonly_fields = ['joined_date']
    
    fieldsets = (
        ('Członkostwo', {
            'fields': ('person', 'community', 'role', 'is_active')
        }),
        ('Informacje', {
            'fields': ('joined_date',)
        }),
    )
    
    # Pokazuj tylko osoby (user_type='person') przy wyborze
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "person":
            kwargs["queryset"] = CustomUser.objects.filter(user_type='person')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    