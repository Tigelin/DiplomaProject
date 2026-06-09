import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

application = get_wsgi_application()

try:
    from whitenoise import WhiteNoise
    
    static_root = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'staticfiles')
    
    if not os.path.exists(static_root):
        os.makedirs(static_root, exist_ok=True)
    
    application = WhiteNoise(application, root=static_root)
    application.add_files(static_root, prefix='static/')
    
except Exception as e:
    print(f"WhiteNoise warning: {e}")