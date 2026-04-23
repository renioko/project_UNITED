"""
Walidatory dla uploadowanych plików
"""
from django.core.exceptions import ValidationError
from django.conf import settings
from PIL import Image
from cloudinary.models import CloudinaryResource


def validate_image_file(image):
    """
    Walidacja uploadowanego obrazka:
    - Rozmiar max 5MB
    - Format: jpg, jpeg, png, gif, webp
    - Czy to faktycznie obrazek (bezpieczeństwo)
    """
    if not image:
        return
    # CloudinaryResource jest już zwalidowany i na serwerze - pomijamy
    if isinstance(image, CloudinaryResource):
        return
    # 1. Sprawdź rozmiar pliku
    max_size = getattr(settings, 'MAX_IMAGE_SIZE', 5 * 1024 * 1024)
    if image.size > max_size:
        max_mb = max_size / 1024 / 1024
        raise ValidationError(
            f'Plik jest za duży ({image.size / 1024 / 1024:.1f}MB). '
            f'Maksymalny rozmiar to {max_mb:.0f}MB.'
        )
    
    # 2. Szybki check rozszerzenia (odrzuć .exe, .pdf etc. od razu)
    allowed_extensions = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    file_extension = image.name.split('.')[-1].lower()
    
    if file_extension not in allowed_extensions:
        raise ValidationError(
            f'Nieprawidłowe rozszerzenie pliku (.{file_extension}). '
            f'Dozwolone: {", ".join(allowed_extensions).upper()}'
        )
    
    # 3. Głęboka walidacja - faktyczny format pliku
    try:
        img = Image.open(image)
        img.verify()
        
        # Reset i ponowne otwarcie
        image.seek(0)
        img = Image.open(image)
        
        # ✅ SPRAWDŹ FAKTYCZNY FORMAT (bezpieczeństwo)
        # UWAGA: Pillow zwraca 'JPEG' nie 'JPG'!
        allowed_formats = ['JPEG', 'PNG', 'GIF', 'WEBP']
        if img.format not in allowed_formats:
            raise ValidationError(
                f'Nieprawidłowy format obrazka ({img.format}). '
                f'Dozwolone: JPEG, PNG, GIF, WEBP'
            )
        
        # Sprawdź wymiary
        if img.width > 5000 or img.height > 5000:
            raise ValidationError(
                f'Obrazek jest za duży ({img.width}x{img.height}px). '
                'Maksymalne wymiary to 5000x5000px.'
            )
            
    except ValidationError:
        raise
    except Exception as e:
        raise ValidationError('Plik nie jest prawidłowym obrazkiem lub jest uszkodzony.')
    
    # Reset file pointer
    image.seek(0)
    
    return image