import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

app = Celery('docuiq')
app.conf.broker_url = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
app.conf.result_backend = os.environ.get('REDIS_URL', 'redis://redis:6379/0')
app.conf.task_routes = {
    'ingest.tasks.*': {'queue': 'ingest'},
}
app.autodiscover_tasks()

