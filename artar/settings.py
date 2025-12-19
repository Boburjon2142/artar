import os
from pathlib import Path
try:
    from dotenv import load_dotenv  # type: ignore
except Exception:  # pragma: no cover
    def load_dotenv(*args, **kwargs):
        return False

BASE_DIR = Path(__file__).resolve().parent.parent
try:
    load_dotenv(BASE_DIR / '.env')
except Exception:
    pass

# Environment helpers
def get_env(name, default=None):
    return os.environ.get(name, default)

SECRET_KEY = get_env('SECRET_KEY', 'dev-secret-key-change-me')
DEBUG = get_env('DEBUG', '1') == '1'
# Default hosts target artar.uz and PythonAnywhere demo; can be overridden via env
_default_hosts = 'artar.uz,www.artar.uz,sinov.pythonanywhere.com,127.0.0.1,localhost'
ALLOWED_HOSTS = [h.strip() for h in get_env('ALLOWED_HOSTS', _default_hosts).split(',') if h]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'crispy_forms',
    'crispy_bootstrap5',

    'catalog',
    'accounts',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'artar.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'catalog.context_processors.nav_categories',
            ],
        },
    },
]

WSGI_APPLICATION = 'artar.wsgi.application'
ASGI_APPLICATION = 'artar.asgi.application'

# Database: configurable via env
# Prefer explicit DB_ENGINE to support aHost MySQL; fallback to Postgres if DB_NAME given; else sqlite
DB_ENGINE = get_env('DB_ENGINE', '').lower()
DB_NAME = get_env('DB_NAME')

def _mysql_db():
    return {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': DB_NAME,
            'USER': get_env('DB_USER', ''),
            'PASSWORD': get_env('DB_PASSWORD', ''),
            'HOST': get_env('DB_HOST', 'localhost'),
            'PORT': get_env('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
            }
        }
    }

def _pg_db():
    return {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': DB_NAME,
            'USER': get_env('DB_USER', ''),
            'PASSWORD': get_env('DB_PASSWORD', ''),
            'HOST': get_env('DB_HOST', 'localhost'),
            'PORT': get_env('DB_PORT', '5432'),
        }
    }

if DB_NAME:
    # Default to PostgreSQL when DB_ENGINE is empty, keep overrides
    if DB_ENGINE in ('', 'postgres', 'postgresql', 'pg'):
        DATABASES = _pg_db()
    elif DB_ENGINE in ('mysql', 'mariadb'):
        DATABASES = _mysql_db()
    else:
        # Unknown value: choose PostgreSQL as default
        DATABASES = _pg_db()
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en'
TIME_ZONE = 'Asia/Tashkent'
USE_I18N = True
USE_TZ = True
LANGUAGES = [('en', 'English')]
LOCALE_PATHS = [BASE_DIR / 'locale']

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Auth
LOGIN_REDIRECT_URL = 'accounts:dashboard'
LOGOUT_REDIRECT_URL = 'catalog:home'
LOGIN_URL = 'login'

# Crispy Forms
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"

# Whitenoise static files in production
try:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
except Exception:
    # Fallback in environments where whitenoise is not installed yet
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'

# CSRF trusted origins from env (comma-separated full origins)
_default_csrf = 'https://artar.uz,https://www.artar.uz,https://sinov.pythonanywhere.com'
CSRF_TRUSTED_ORIGINS = [o.strip() for o in get_env('CSRF_TRUSTED_ORIGINS', _default_csrf).split(',') if o]

# Security headers for production
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = get_env('SECURE_SSL_REDIRECT', '1') == '1'
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(get_env('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

# Basic logging to console
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Telegram bot config (used for order notifications)
TELEGRAM_BOT_TOKEN = get_env('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = get_env('TELEGRAM_CHAT_ID', '')

# OpenAI moderation
OPENAI_API_KEY = get_env('OPENAI_API_KEY', '')
MODERATION_ENABLED = bool(OPENAI_API_KEY)
MODERATION_THRESHOLD = float(get_env('MODERATION_THRESHOLD', '0.2'))
MODERATION_DUP_THRESHOLD = float(get_env('MODERATION_DUP_THRESHOLD', '0.9'))
