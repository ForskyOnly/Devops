from .base import *
import os
import dj_database_url

SECRET_KEY = os.getenv('SECRET_KEY')


DEBUG = False

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

