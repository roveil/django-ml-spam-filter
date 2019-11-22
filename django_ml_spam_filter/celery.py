import os
from celery import Celery

from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'django_ml_spam_filter.settings')
celery_app = Celery()
celery_app.config_from_object(settings)
celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
