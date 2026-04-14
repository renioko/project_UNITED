from django.contrib import admin
from .models import Event, EventCommunity, EventRole, Announcement, Follow


# ===========================================================================
# EVENT
# ===========================================================================

class EventCommunityInline(admin.TabularInline):
    """Wspólnoty organizujące - inline w widoku eventu."""
    model = EventCommunity
    extra = 1
    fields = ['community', 'role']


class EventRoleInline(admin.TabularInline):
    """Koordynatorzy eventu - inline w widoku eventu."""
    model = EventRole
    extra = 1
    fields = ['user', 'role']


class AnnouncementInline(admin.TabularInline):
    """Ogłoszenia powiązane z eventem - inline w widoku eventu."""
    model = Announcement
    extra = 0
    fields = ['title', 'is_public', 'created_by']
    readonly_fields = ['created_by']
    show_change_link = True


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'date_start', 'date_end', 'location', 'is_public', 'created_by']
    list_filter = ['is_public', 'date_start']
    search_fields = ['title', 'description', 'location']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [EventCommunityInline, EventRoleInline, AnnouncementInline]

    fieldsets = (
        ('Podstawowe informacje', {
            'fields': ('title', 'description', 'is_public')
        }),
        ('Czas i miejsce', {
            'fields': ('date_start', 'date_end', 'location')
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ===========================================================================
# ANNOUNCEMENT
# ===========================================================================

@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ['title', 'community', 'event', 'is_public', 'created_by', 'created_at']
    list_filter = ['is_public', 'created_at']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Treść', {
            'fields': ('title', 'content', 'is_public')
        }),
        ('Powiązanie (wypełnij tylko jedno)', {
            'fields': ('community', 'event'),
            'description': 'Ogłoszenie musi dotyczyć wspólnoty LUB wydarzenia – nie obu naraz.',
        }),
        ('Meta', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


# ===========================================================================
# FOLLOW
# ===========================================================================

@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    list_display = ['user', 'community', 'event', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'community__name', 'event__title']
    readonly_fields = ['created_at']