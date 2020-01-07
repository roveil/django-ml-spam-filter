SECRET_KEY = 'yourappsecret'
DEBUG = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'testdb',
        'USER': 'test',
        'PASSWORD': 'testpass',
        'HOST': 'localhost',
        'PORT': '5432',
        'CONN_MAX_AGE': 60
    }
}

CACHEOPS_REDIS = {
    'host': 'localhost',
    'port': 6379,
    'db': 13,
    'socket_timeout': 3,
}

BROKER_URL = 'amqp://127.0.0.1/'

CELERY_QUEUE = 'spam_filter_main'

STATSD_HOST = '127.0.0.1'
STATSD_PORT = 8125
STATSD_PREFIX = None

SECURE_TOKEN = 'testtoken123'

# SENTRY
#SENTRY_SDK_DSN_URL = "https://pathtoyoursentryapp.com"
