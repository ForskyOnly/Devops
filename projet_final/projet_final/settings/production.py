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

DEBUG = False
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_HTTPONLY = True
CSRF_USE_SESSIONS = True 
CSRF_TRUSTED_ORIGINS = [
    'https://*.bref-board.azurewebsites.net',
    'https://bref-board.azurewebsites.net',
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://0.0.0.0:8000/',
]


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE'),
        'USER': 'rubic',
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'OPTIONS': {
             'ssl': {'disabled': True},  
        },
    }
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')