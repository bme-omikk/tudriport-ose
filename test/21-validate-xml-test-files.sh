#!/bin/bash

DIRNAME=$(readlink -f $(dirname $0))
TESTBASEDIR=$DIRNAME
BASEDIR=$DIRNAME/..

. $DIRNAME/lib/validate-xml-against-schema.sh

# we will track last non-0 exit status here
RETVAL=0

for f in $TESTBASEDIR/resources/mtmt1-xml/*.xml ; do
  validateXmlAgainstSchema $DIRNAME/assets/mycite.xsd $f

  L_RETVAL=$?
  if [ "${L_RETVAL}x" != "0x" ]; then
    RETVAL=$L_RETVAL
  fi
done

exit $RETVAL
