from .base import *
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="/home/utilisateur/Documents/dev/devia/Devops/projet_final/.env")

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
API_KEY_NAME = os.getenv('API_KEY_NAME')
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')
RESOURCE_GROUP = os.getenv('RESOURCE_GROUP')
LOCATION = os.getenv('LOCATION')
SERVER_NAME = os.getenv('SERVER_NAME')
SUBSCRIPTION_ID = os.getenv('SUBSCRIPTION_ID')

DEBUG = True

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


# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }