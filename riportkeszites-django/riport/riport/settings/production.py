from .base import getconfig
from .base import *  # noqa


DEBUG = False

# ######### EMAIL CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-host
EMAIL_HOST = getconfig('email.host')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-port
EMAIL_PORT = getconfig('email.port')

# See: https://docs.djangoproject.com/en/dev/ref/settings/#email-use-tls
EMAIL_USE_TLS = False

SERVER_EMAIL = DEFAULT_FROM_EMAIL
# ######### END EMAIL CONFIGURATION

# ######### SECRET CONFIGURATION
# See: https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = getconfig('django.secret_key')
# ######### END SECRET CONFIGURATION

ADMINS = tuple(
    (s[0], s[1])
    for s in map(lambda x: x.split("|"), getconfig("django.admins").split(","))
)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s %(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': getconfig("django.logfile"),
            'formatter': 'verbose',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 10
        },
        'file-misc': {
            'level': 'DEBUG',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': getconfig("django.logfile-misc"),
            'formatter': 'verbose',
            'maxBytes': 1024 * 1024 * 50,
            'backupCount': 10
        },
        'console': {
            'class': 'logging.StreamHandler',
        },
        'console-error': {
            'level': 'ERROR',
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['file-misc', 'console-error'],
         'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'WARNING',
            'propagate': True,
        },
        'db.sources': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'riport.management.commands.ext_authorlist': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}
