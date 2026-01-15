from django.shortcuts import render, get_object_or_404
from .models import CommunityProfile, Tag

def home(request):
    """Strona główna"""
    return render(request, 'communities/home.html')

def community_list(request):
    """Lista wspólnot"""
    communities = CommunityProfile.objects.filter(is_active=True)
    tags = Tag.objects.all()
    
    # Proste filtrowanie (później rozbudujemy)
    city_filter = request.GET.get('city')
    if city_filter:
        communities = communities.filter(city__icontains=city_filter)
    
    context = {
        'communities': communities,
        'tags': tags,
    }
    return render(request, 'communities/community_list.html', context)

def community_detail(request, pk):
    """Szczegóły wspólnoty"""
    community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
    members = community.memberships.filter(is_active=True).select_related('person')
    
    context = {
        'community': community,
        'members': members,
    }
    return render(request, 'communities/community_detail.html', context)


## **Teraz templates - najprostsza wersja:**

# **Struktura folderów:**
# ```
# communities/
# └── templates/
#     └── communities/
#         ├── base.html           # Bazowy template
#         ├── home.html           # Strona główna
#         ├── community_list.html # Lista
#         └── community_detail.html # Szczegóły