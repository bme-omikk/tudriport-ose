#!/bin/bash
# This script should be ran from git root.
set -o errexit
set -o xtrace

PYTHON_EXE=/usr/bin/python3

# install packages
sudo apt-get install postgresql python3 python3-pip libapache2-mod-wsgi-py3 libpq-dev npm -y

# create virtualenv
virtualenv -p $PYTHON_EXE env

# install requirements
. env/bin/activate
pip install -r requirements.txt

# build angular
cd riportkeszites-angular
## use package-lock.json
npm ci
## if using package.json instead:
#npm install @angular/cli
#npm install
## build the Angular app
node_modules/.bin/ng build --base-href=/tudriport/ --prod
cd ..

# initialize django
# it is recommended to use install-time configuration for django initialization/migration
#export DJANGO_SETTINGS_MODULE=riport.settings.install
cd riportkeszites-django/riport
python manage.py migrate
python manage.py create_default_groups
python manage.py collectstatic -v 0 --no-input --clear
python manage.py seeddb
cd ../..
