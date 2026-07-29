from .base import *  # noqa
from .base import DATABASES, getconfig

# use same database as configured in config file
DATABASES['default']['TEST'] = {'NAME': getconfig('db.SQLDB')}