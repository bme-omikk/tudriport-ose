#!/bin/bash

# validate a given XML file (arg#2) against an XML schema (arg#1)
# and output any validation error found
# if 3rd parameter (FANCY) is set to yes (default, if omitted), failing file header and separators will also be printed.
function validateXmlAgainstSchema {
  P_XSD_FILE=$1
  P_XML_FILE=$2
  P_FANCY=${3:-"yes"}

  L_STDOUT=$(xmllint --noout --schema ${P_XSD_FILE} ${P_XML_FILE} 2>&1)
  L_RETVAL=$?
  if [ "${L_RETVAL}x" != "0x" ]; then
    if [ "${P_FANCY}x" == "yesx" ]; then
      cat <<HERE >&2
===========>%===========>%========
FAILED validation or parsing. XSD was: `basename ${P_XSD_FILE}`
  failing XML file: ${P_XML_FILE}
----------------------------------
HERE
    fi

    echo "${L_STDOUT}" >&2

    if [ "${P_FANCY}x" == "yesx" ]; then
      cat <<HERE >&2
===========>%===========>%========
HERE
    fi
  fi

  return ${L_RETVAL}
}
