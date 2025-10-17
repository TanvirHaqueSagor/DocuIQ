try:
    from .celery import app as celery_app  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback for test environments
    celery_app = None
