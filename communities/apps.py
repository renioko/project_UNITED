from django.apps import AppConfig


class CommunitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'communities'
    verbose_name = 'Wspólnoty'  # Opcjonalnie - ładna nazwa w adminie

    def ready(self):
        """
        Metoda wywoływana gdy aplikacja jest gotowa.
        Tu importujemy sygnały, żeby Django je załadował.
        
        WAŻNE: Import MUSI być tutaj (nie na górze pliku),
        żeby uniknąć circular imports.
        """
        import communities.signals  # noqa (importuj sygnały)