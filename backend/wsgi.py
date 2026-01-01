import os
from django.core.wsgi import get_wsgi_application

# POINT THIS TO 'core.settings' BECAUSE THAT IS WHERE YOUR SETTINGS FILE IS!
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()