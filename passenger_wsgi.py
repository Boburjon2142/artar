import sys, os

# ==== 1) LOYIHA YO‘LI ====
PROJECT_DIR = '/home/artaruz/artar_app'
sys.path.insert(0, PROJECT_DIR)

# ==== 2) VIRTUALENV YO‘LI ====
VENV_PATH = '/home/artaruz/virtualenv/artar_app/3.12'
activate_this = os.path.join(VENV_PATH, 'bin/activate_this.py')
with open(activate_this) as f:
    exec(f.read(), {'__file__': activate_this})

# ==== 3) DJANGO SETTINGS ====
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "artar.settings")

# ==== 4) DJANGO APPLICATION ====
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
