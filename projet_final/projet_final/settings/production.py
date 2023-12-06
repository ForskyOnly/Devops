from .base import *
import os
import dj_database_url
from dotenv import load_dotenv
load_dotenv()


SECRET_KEY = os.getenv('SECRET_KEY')


DEBUG = False

DATABASES = {
    'default': dj_database_url.config(default=os.getenv('DATABASE_URL'))
}

