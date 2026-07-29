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

for f in $TESTBASEDIR/resources/authors/*.txt ; do
  echo "===== Testing " $(basename $f)

  filename=$(basename -- "$f")
  filename="${filename%.*}"

  IFS='_' read -ra ADDR <<< $filename

  riportkeszites-django/riport/manage.py ext_authorlist --file $f --org ${ADDR[0]} --unit ${ADDR[1]} --subunit ${ADDR[2]}
  L_RETVAL=$?

  if [ "${L_RETVAL}x" != "0x" ]; then
    RETVAL=$L_RETVAL
  fi
done

exit $RETVAL
