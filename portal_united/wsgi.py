"""
WSGI config for portal_united project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import time
from pathlib import Path
from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portal_united.settings')

# Poczekaj 3 sekundy na bazę danych (Railway workaround)
time.sleep(3)
# === DEBUG - usuń to potem ===
static_root = Path('/app/staticfiles')
if static_root.exists():
    file_count = sum(1 for _ in static_root.rglob('*') if _.is_file())
    print(f"✅ /app/staticfiles/ EXISTS with {file_count} files")
    # Pokaż pierwsze 10 plików
    for i, f in enumerate(static_root.rglob('*')):
        if i > 10: break
        print(f"  - {f}")
else:
    print("❌ /app/staticfiles/ DOES NOT EXIST!")
# === END DEBUG ===

application = get_wsgi_application()