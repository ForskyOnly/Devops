from .base import *
import os
import dj_database_url
from dotenv import load_dotenv
load_dotenv()



SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = False
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_SECURE = True
CSRF_TRUSTED_ORIGINS = ['https://*.bref-board.azurewebsites.net/']


DATABASES = {
    'default': dj_database_url.config(
        default=f"mysql://{os.getenv('USERNAME')}:{os.getenv('PASSWORD')}@{os.getenv('SERVER_NAME')}.mysql.database.azure.com/{os.getenv('DATABASE')}?ssl-mode=DISABLED"
    )
}

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
