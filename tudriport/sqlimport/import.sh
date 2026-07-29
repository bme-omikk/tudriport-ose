#!/bin/bash

cd $(dirname $0)

if [ -z $1 ]; then
    echo 'Modulok (1. argumentum):' `ls -1 importlib/*.py | grep -v __init__ | xargs -l1 basename -s .py`
else
    cd ../..
    python3 -m tudriport.sqlimport.importlib.$@
fi
