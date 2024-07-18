from .base import *
from dotenv import load_dotenv
import os

load_dotenv(dotenv_path="/home/utilisateur/Documents/dev/devia/Devops/projet_final/.env")

SECRET_KEY = os.getenv('SECRET_KEY', default='notsecret')

DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.getenv('DATABASE'),
        'USER': os.getenv('USERNAME'),
        'PASSWORD': os.getenv('PASSWORD'),
        'HOST': os.getenv('DATABASE_HOST'),
        'PORT': os.getenv('DATABASE_PORT'),
        'OPTIONS': {
             'ssl': {'disabled': True},  # Comment out or remove this line
        },
    }
}
