import os
from django.core.wsgi import get_wsgi_application
from whitenoise import WhiteNoise
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

application = WhiteNoise(
    application,
    root=settings.STATIC_ROOT,
    prefix='static/'
)

if settings.STATICFILES_DIRS:
    for static_dir in settings.STATICFILES_DIRS:
        application.add_files(static_dir, prefix='static/')