from re import T
from .base import *
import os
import dj_database_url
from dotenv import load_dotenv
load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
API_KEY_NAME = os.getenv('API_KEY_NAME')
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
RESOURCE_GROUP = os.getenv('RESOURCE_GROUP')
LOCATION = os.getenv('LOCATION')
SERVER_NAME = os.getenv('SERVER_NAME')
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')
SECRET_KEY = os.environ.get('SECRET_KEY')

DEBUG = False
CSRF_COOKIE_SECURE = False  # Changé à False car nous n'utilisons pas HTTPS
SESSION_COOKIE_SECURE = False  # Changé à False car nous n'utilisons pas HTTPS
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True 

SECURE_PROXY_SSL_HEADER = None
SECURE_SSL_REDIRECT = False


CONTAINER_URL = f'http://{os.environ.get("WEBSITE_HOSTNAME", "bref-board-dns.francecentral.azurecontainer.io")}'
CSRF_TRUSTED_ORIGINS = [
    CONTAINER_URL,
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000/',
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE'),
        'USER': os.getenv('NOMUSER'),  
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'OPTIONS': {
             'ssl': {'disabled': True},  
        },
    }
}

if os.environ.get('DJANGO_TEST_MODE') == 'True':
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }

STATIC_ROOT = os.path.join(BASE_DIR.parent, 'BrefBoard', 'staticfiles')

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'