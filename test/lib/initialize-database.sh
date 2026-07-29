#!/bin/bash

# initialize database, dropping it if it existed before
#  - database name: arg#1, default do $MY_DB_NAME
#  - database owner: arg#2, default to $MY_DB_USER
function initializeDatabase {
  P_DB_NAME=${1:-"${MY_DB_NAME}"}
  P_DB_USER=${2:-"${MY_DB_USER}"}
  P_DB_HOST=${3:-"${MY_DB_HOST}"}

  dropdb   -w -U postgres -h $P_DB_HOST --if-exists $P_DB_NAME
  createdb -w -U postgres -h $P_DB_HOST  $P_DB_NAME -T template0 -E UTF8 -l hu_HU.UTF-8 -O $P_DB_USER

  pushd $BASEDIR/riportkeszites-django/riport
  python manage.py migrate
  python manage.py create_default_groups
  python manage.py collectstatic -v 0 --no-input --clear
  python manage.py seeddb
  popd
}
