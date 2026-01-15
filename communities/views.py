# from django.shortcuts import render, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView
from django.db.models import Q
from .models import CommunityProfile, Tag

class HomeView(TemplateView):
    """Strona główna"""
    template_name = 'communities/home.html'

# def home(request):
#     """Strona główna"""
#     return render(request, 'communities/home.html')

class CommunityListView(ListView):
    """Lista wspólnot"""
    model = CommunityProfile
    template_name = 'communities/community_list.html'
    context_object_name = 'communities'
    paginate_by = 12  # 12 wspólnot na stronę

    def get_queryset(self):
        """Filtrowanie wspólnot"""
        queryset = CommunityProfile.objects.filter(is_active=True).select_related('user')
        
        # Filtrowanie po mieście
        city = self.request.GET.get('city')
        if city:
            queryset = queryset.filter(city__icontains=city)
        
        # Filtrowanie po denominacji
        denomination = self.request.GET.get('denomination')
        if denomination:
            queryset = queryset.filter(denomination=denomination)
        
        # Filtrowanie po tagach
        tag_slug = self.request.GET.get('tag')
        if tag_slug:
            queryset = queryset.filter(tags__slug=tag_slug)
        
        # Wyszukiwanie po nazwie
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(description__icontains=search)
            )
        
        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        """Dodatkowe dane do template"""
        context = super().get_context_data(**kwargs)
        context['tags'] = Tag.objects.all()
        context['denominations'] = CommunityProfile.DENOMINATION_CHOICES
        return context
    
# def community_list(request):
#     """Lista wspólnot"""
#     communities = CommunityProfile.objects.filter(is_active=True)
#     tags = Tag.objects.all()
    
#     # Proste filtrowanie (później rozbudujemy)
#     city_filter = request.GET.get('city')
#     if city_filter:
#         communities = communities.filter(city__icontains=city_filter)
    
#     context = {
#         'communities': communities,
#         'tags': tags,
#     }
#     return render(request, 'communities/community_list.html', context)

class CommunityDetailView(DetailView):
    """Szczegóły wspólnoty"""
    model = CommunityProfile
    template_name = 'communities/community_detail.html'
    context_object_name = 'community'
    
    def get_queryset(self):
        """Tylko aktywne wspólnoty"""
        return CommunityProfile.objects.filter(is_active=True).select_related('user').prefetch_related('tags')
    
    def get_context_data(self, **kwargs):
        """Dodaj członków do kontekstu"""
        context = super().get_context_data(**kwargs)
        context['members'] = self.object.memberships.filter(
            is_active=True
        ).select_related('person__person_profile').order_by('-joined_date')
        return context

# def community_detail(request, pk):
#     """Szczegóły wspólnoty"""
#     community = get_object_or_404(CommunityProfile, pk=pk, is_active=True)
#     members = community.memberships.filter(is_active=True).select_related('person')
    
#     context = {
#         'community': community,
#         'members': members,
#     }
#     return render(request, 'communities/community_detail.html', context)

# ====================================================
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