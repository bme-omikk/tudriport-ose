#!/bin/bash

DIRNAME=$(readlink -f $(dirname $0))
TESTBASEDIR=$DIRNAME
BASEDIR=$DIRNAME/..

. $DIRNAME/lib/initialize-database.sh

set -e

# we will track last non-0 exit status here
RETVAL=0

echo "===== Initializing database "
initializeDatabase

# test with *.json and packed *.json.xz, *.json.gz files
for f in $TESTBASEDIR/resources/mtmt2-json/*.json* ; do
  echo "===== Testing " $(basename $f)

  /usr/bin/env python3 riportkeszites-django/riport/manage.py file2db --trydebug -M2 $f
  L_RETVAL=$?

  if [ "${L_RETVAL}x" != "0x" ]; then
    RETVAL=$L_RETVAL
  fi
done

exit $RETVAL


