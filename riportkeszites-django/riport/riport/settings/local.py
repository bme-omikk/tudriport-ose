from .base import *  # noqa

from .base import INSTALLED_APPS

DEBUG = True

INSTALLED_APPS += (
    'django_extensions',
)

CORS_ORIGIN_ALLOW_ALL = True
CSRF_TRUSTED_ORIGINS = ('localhost:4200', )
CORS_ALLOW_CREDENTIALS = True