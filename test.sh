#!/bin/sh
SCRIPT_DIR=$( cd "$( dirname "$0" )" && pwd )
export PYTHONPATH=$PYTHONPATH:$SCRIPT_DIR
nosetests -w pyjade/testsuite/ -v
