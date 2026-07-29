import os

from tudriport.common.config import getconfig

def get_app_user():
    # use Django user if available
    return os.environ.get('DJANGO_USER', getconfig('db.defaultAppUser'))
