import os
import re
import logging

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = os.environ.get('SECRET_KEY', 'changeme')

DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "").split(",")

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'accounts',
    'documents',
    'ingest',
    'chats',
]

MIDDLEWARE = [
    'core.middleware.SubdomainTenantMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# লোকালের জন্য দারুণ: 127.0.0.1.nip.io (যে কোনো সাবডোমেইন লোকালেই রেজল্ভ হবে)
ROOT_DOMAIN = os.environ.get('ROOT_DOMAIN', '127.0.0.1.nip.io')

ROOT_URLCONF = 'core.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [os.path.join(BASE_DIR, 'templates')],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ],},
}]

WSGI_APPLICATION = 'core.wsgi.application'

DATABASES = {
  "default": {
    "ENGINE": "django.db.backends.postgresql",
    "NAME": os.environ.get("POSTGRES_DB", "docuiq"),
    "USER": os.environ.get("POSTGRES_USER", "docuadmin"),
    "PASSWORD": os.environ.get("POSTGRES_PASSWORD", "securepassword"),
    "HOST": os.environ.get("DB_HOST", "docuiqdb"),
    "PORT": os.environ.get("DB_PORT", "5432"),
    "CONN_MAX_AGE": 60,
  }
}

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
MEDIA_URL = '/media/'
# Ensure media files live under /app/media inside the container.
# Our code is mounted at /app (BASE_DIR), so put media alongside it.
# This avoids writing to container root (/media) which breaks across services.
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ----- Logging -----
# Log file directory configurable via LOG_DIR; defaults to /app/logs
LOG_DIR = os.environ.get('LOG_DIR', os.path.join(BASE_DIR, 'logs'))
try:
    os.makedirs(LOG_DIR, exist_ok=True)
except Exception:
    # Fallback to base dir if cannot create; prevents startup crash
    LOG_DIR = BASE_DIR

LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO').upper()
_fmt = '[%(asctime)s] %(levelname)s %(name)s: %(message)s'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': _fmt,
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file_app': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(LOG_DIR, 'app.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': int(os.environ.get('LOG_BACKUPS', 7)),
            'encoding': 'utf-8',
        },
        'file_celery': {
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'formatter': 'standard',
            'filename': os.path.join(LOG_DIR, 'celery.log'),
            'when': 'midnight',
            'interval': 1,
            'backupCount': int(os.environ.get('LOG_BACKUPS', 7)),
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file_app'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'ingest': {
            'handlers': ['console', 'file_app'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        'celery': {
            'handlers': ['console', 'file_celery'],
            'level': LOG_LEVEL,
            'propagate': False,
        },
        # Catch-all
        '': {
            'handlers': ['console', 'file_app'],
            'level': LOG_LEVEL,
        },
    },
}

# Allow embedding media/PDFs in iframe during development for the document viewer
# Allow embedding media/PDFs in iframe for the document viewer
X_FRAME_OPTIONS = 'ALLOWALL'

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOW_CREDENTIALS = True

CORS_ALLOWED_ORIGIN_REGEXES = [
    "^https?://([a-z0-9-]+\.)?{}(?::\d+)?$".format(re.escape(ROOT_DOMAIN)),
    r"^http://localhost(?::\d+)?$",
    r"^http://127\.0\.0\.1(?::\d+)?$",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_PARSER_CLASSES': (
        'rest_framework.parsers.JSONParser',
        'rest_framework.parsers.FormParser',
        'rest_framework.parsers.MultiPartParser',
    ),
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
}

from datetime import timedelta
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=30),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
