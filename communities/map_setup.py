# ===========================================================================
# KROK 1: Dodaj do modelu CommunityProfile w communities/models.py
# ===========================================================================

# Dodaj te dwa pola do klasy CommunityProfile (np. po polu 'website'):

latitude = models.DecimalField(
    max_digits=9,
    decimal_places=6,
    null=True,
    blank=True,
    verbose_name='Szerokość geograficzna',
)
longitude = models.DecimalField(
    max_digits=9,
    decimal_places=6,
    null=True,
    blank=True,
    verbose_name='Długość geograficzna',
)

# Potem uruchom:
# python manage.py makemigrations communities
# python manage.py migrate


# ===========================================================================
# KROK 2: Dodaj CommunityMapView do communities/views.py
# ===========================================================================

import json
from django.http import JsonResponse

class CommunityMapView(View):
    """
    Widok mapy wspólnot.
    GET /communities/map/ → strona z mapą
    GET /communities/map/data/ → JSON z danymi wspólnot (dla filtrowania AJAX)
    """
    template_name = 'communities/community_map.html'

    def get(self, request):
        # Pobierz wszystkie aktywne wspólnoty z lokalizacją
        communities = CommunityProfile.objects.filter(
            is_active=True,
            latitude__isnull=False,
            longitude__isnull=False,
        ).prefetch_related('tags')

        # Filtrowanie po tagach (opcjonalne)
        tag_slug = request.GET.get('tag')
        if tag_slug:
            communities = communities.filter(tags__slug=tag_slug)

        # Przygotuj dane JSON dla mapy
        communities_json = []
        for c in communities:
            communities_json.append({
                'id': c.pk,
                'name': c.name,
                'city': c.city,
                'lat': float(c.latitude),
                'lng': float(c.longitude),
                'denomination': c.get_denomination_display(),
                'tags': [t.name for t in c.tags.all()],
                'logo': c.logo.url if c.logo else None,
                'url': f'/communities/{c.pk}/',
                'description': c.description[:100] + '...' if len(c.description) > 100 else c.description,
            })

        # Wszystkie tagi do filtrowania
        all_tags = Tag.objects.filter(
            communities__is_active=True,
            communities__latitude__isnull=False,
        ).distinct()

        context = {
            'communities_json': json.dumps(communities_json, ensure_ascii=False),
            'all_tags': all_tags,
            'selected_tag': tag_slug,
            'GOOGLE_MAPS_API_KEY': settings.GOOGLE_MAPS_API_KEY,
        }
        return render(request, self.template_name, context)


# ===========================================================================
# KROK 3: Dodaj do communities/urls.py
# ===========================================================================

# path('communities/map/', views.CommunityMapView.as_view(), name='community_map'),


# ===========================================================================
# KROK 4: Dodaj do settings.py
# ===========================================================================

# GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')
# I dodaj do .env:
# GOOGLE_MAPS_API_KEY=twój_klucz_api