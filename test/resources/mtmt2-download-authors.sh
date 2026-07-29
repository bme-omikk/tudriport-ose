#!/bin/bash

# Lekerdezi a szerzo vagy szerzok kozlemenyeit az MTMT2-bol
#
# 1. parameter: egy szerzo MTID-je vagy MTID:NevSzokozok_Nelkul, vagy egy fajl, ami soronkent ilyen bejegyzeseket tartalmaz
#               ha ures vagy hianyzik, akkor a script melletti mtmt2-authors.list fajlt hasznalja
#
# 2. parameter: ha "force", akkor mindenkeppen letolti az allomanyt, egyebkent ha mar lezetik a fajl, akkor nem toltodik le

DIRNAME=$(readlink -f $(dirname $0))
BASEDIR=$DIRNAME/../..
OUTPUT_DIR=$DIRNAME/mtmt2-json

export PYTHONPATH=$BASEDIR/tudriport/common

FNAME_PREFIX=tmp_kozlemeny_

P_URL=$($BASEDIR/tudriport/common/config.py -k input_sources.mtmt2.author-all)
P_SOURCE=${1:-$DIRNAME/mtmt2-authors.list}
P_FORCE=${2}

if [ -f $P_SOURCE ]; then
  for line in $(grep -v '^#' $P_SOURCE | grep -v '^\s*$'); do
    L_MTID=$(echo $line | cut -d: -f1)
    L_NAME=$(echo $line | cut -d: -f2)
    if [ "${L_NAME}x" == "x" ]; then
      L_NAME=$L_MTID
    fi
    L_URL=$(echo $P_URL | sed -e "s/@@@/$L_MTID/")
    L_FNAME=$OUTPUT_DIR/${FNAME_PREFIX}${L_NAME}.json

    if [ "${P_FORCE}x" == "forcex" -o ! -f ${L_FNAME}.gz ]; then
      wget --compression=gzip -O $L_FNAME ''''$L_URL''''
      gzip -f $L_FNAME
    else
      echo "File already exists. To re-download, delete the file or add 'force' as 2nd parameter: ${L_FNAME}.gz "
    fi
  done
else
    line=$P_SOURCE

    L_MTID=$(echo $line | cut -d: -f1)
    L_NAME=$(echo $line | cut -d: -f2)
    if [ "${L_NAME}x" == "x" ]; then
      L_NAME=$L_MTID
    fi
    L_URL=$(echo $P_URL | sed -e "s/@@@/$L_MTID/")
    L_FNAME=$OUTPUT_DIR/${FNAME_PREFIX}${L_NAME}.json

    if [ "${P_FORCE}x" == "forcex" -o ! -f ${L_FNAME}.gz ]; then
      wget --compression=gzip -O $L_FNAME ''''$L_URL''''
      gzip -f $L_FNAME
    else
      echo "File already exists. To re-download, delete the file or add 'force' as 2nd parameter: ${L_FNAME}.gz "
    fi
fi
