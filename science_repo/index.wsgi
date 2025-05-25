import os
import sys

# Füge dein Projekt zum Python-Pfad hinzu
sys.path.insert(0, '/var/www/html/srahmel/price-machine.shop')
sys.path.insert(0, '/var/www/html/srahmel/price-machine.shop/science_repo')

# Setze Settings-Modul
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "science_repo.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
