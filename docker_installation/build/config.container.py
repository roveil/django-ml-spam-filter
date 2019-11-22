import os

SECRET_KEY = os.environ.get('SECRET_KEY', '')
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.environ.get('POSTGRES_DB', 'docker'),
        'USER': os.environ.get('POSTGRES_USER', 'docker'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'docker'),
        'HOST': os.environ.get('POSTGRES_HOST', 'docker'),
        'PORT': int(os.environ.get('POSTGRES_PORT', '5432')),
        'CONN_MAX_AGE': 60
    }
}

CACHEOPS_ENABLED = True
CACHEOPS_REDIS = {
    'host': os.environ.get('REDIS_HOST', 'redis'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': 13,
    'socket_timeout': 3,
}

BROKER_URL = 'amqp://{user}:{password}@{hostname}/{vhost}'.format(
  hostname=os.environ.get('RABBITMQ_HOST', 'rabbitmq'),
  user=os.environ.get('RABBITMQ_DEFAULT_USER', 'admin'),
  password=os.environ.get('RABBITMQ_DEFAULT_PASS', 'pass'),
  vhost=os.environ.get('RABBITMQ_DEFAULT_VHOST', '/'))

CELERY_QUEUE = os.environ.get('CELERY_QUEUE', 'spam_filter_main')

REDIS_SETTINGS = {
    'host': os.environ.get('REDIS_HOST', 'redis'),
    'port': int(os.environ.get('REDIS_PORT', 6379)),
    'db': 10,
    'socket_timeout': 10,
    'password': None
}

STATSD_HOST = os.environ.get('STATSD_HOST', 'localhost')
STATSD_PORT = int(os.environ.get('STATSD_PORT', 8125))
STATSD_PREFIX = os.environ.get('STATSD_PREFIX', None)

SECURE_TOKEN = os.environ.get('SECURE_TOKEN', 'test_token')

NUM_CPU_CORES = int(os.environ.get('NUM_CPU_CORES', 4))

# SENTRY
SENTRY_SDK_DSN_URL = os.environ.get('SENTRY_SDK_DSN_URL', '')
