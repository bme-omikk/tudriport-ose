#!/bin/bash
# script to run input queue processor
# this can be invoked in a screen, like screen -D -m /path/to/repo/

# this makes the command wrapper to leave DJANGO_SETTING_MODULE unset if it was unset
export COMMAND_WRAPPER_OVERRIDE_DJANGO_SETTINGS=no

# make sure to change to repository root directory
# FIXME: this is necessary because of old logging facility in the import uses relative path definitions
cd $(dirname $(dirname $0))

$(dirname $0)/command_wrapper.sh input_queue_processor --sourceid mtmt2 --author --publication --continuous
