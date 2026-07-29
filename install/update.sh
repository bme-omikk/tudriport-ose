#!/bin/bash
# This script should be ran from git root.
# This script installs all dependencies and runs django migrations.
set -o errexit
set -o xtrace

# install requirements
. env/bin/activate
pip install -r requirements.txt

# initialize django
# it is recommended to use install-time configuration for django initialization/migration
#export DJANGO_SETTINGS_MODULE=riport.settings.install
cd riportkeszites-django/riport
python manage.py migrate
python manage.py collectstatic -v 0 --no-input --clear
python manage.py seeddb
cd ../..

# touch WSGI script to trigger code reload in the webserver/WSGI module
touch ./riportkeszites-django/riport/riport/wsgi.py
