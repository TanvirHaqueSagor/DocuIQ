import os
from .settings import *  # noqa: F401,F403

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "test.sqlite3"),  # type: ignore[name-defined]
    }
}

PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
ROOT_DOMAIN = "example.com"

CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

TEST_MEDIA_ROOT = os.path.join(BASE_DIR, "test_media")  # type: ignore[name-defined]
os.makedirs(TEST_MEDIA_ROOT, exist_ok=True)
MEDIA_ROOT = TEST_MEDIA_ROOT

AI_ENGINE_URL = "http://testserver/ai"

ALLOWED_HOSTS = ["testserver", "localhost", "127.0.0.1", "example.com", ".example.com"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
