#!/bin/bash

DIRNAME=$(readlink -f $(dirname $0))
TESTBASEDIR=$DIRNAME
BASEDIR=$DIRNAME/..

. $DIRNAME/lib/initialize-database.sh

set -e

initializeDatabase
