#!/bin/bash
# general wrapper to run django commands
#
# if used directly, i.e. using command_wrapper as call name,
#    all arguments are passed to the manage.py, so the first argument will be the command name
#    and further arguments will be the command's arguments
# if used through a symlink, then command name will be the symlink basename (without .sh ending),
#    and all further arguments are passed to the command.
#
# exit code is passed back from the command.
#
# Django settings module used for command execution:
#    - when DJANGO_SETTINGS_MODULE is set, it will be left intact
#    - when DJANGO_SETTINGS_MODULE is unset, then it will be overridden for console logging
#      (riport.settings.log_to_console). This overriding can be disabled by setting 
#      COMMAND_WRAPPER_OVERRIDE_DJANGO_SETTINGS environment variable to "no".
#      This way, the default settings module will be used.
#
#
# Example: if there is a symlink mycommand.sh pointing to this wrapper,
#    then the two forms below are equivalent:
#      ./command_wrapper.sh mycommand foo bar
#      ./mycommand.sh foo bar
#    Both forms will call the manage.py of the django application as follows:
#      python3 path/to/manage.py mycommand foo bar

CALLNAME=$0
CALLNAME_BASENAME=$(basename $0 .sh)

CANONICAL_NAME=$(readlink -f $0)
CANONICAL_BASENAME=$(basename $CANONICAL_NAME .sh)

if ! [ -v DJANGO_SETTINGS_MODULE ]; then
  if [ "${COMMAND_WRAPPER_OVERRIDE_DJANGO_SETTINGS}x" != "nox" ]; then
    export DJANGO_SETTINGS_MODULE=riport.settings.log_to_console
  fi
fi

REPOSITORY_ROOTDIR=$(dirname $(dirname $CANONICAL_NAME))
source "${REPOSITORY_ROOTDIR}/env/bin/activate"

if [ "${CALLNAME_BASENAME}x" == "${CANONICAL_BASENAME}x" ]; then
  python3 "${REPOSITORY_ROOTDIR}/riportkeszites-django/riport/manage.py" $*
  exit $?
else
  python3 "${REPOSITORY_ROOTDIR}/riportkeszites-django/riport/manage.py" $CALLNAME_BASENAME $*
  exit $?
fi


