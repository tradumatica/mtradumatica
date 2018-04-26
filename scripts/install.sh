#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

if [ ! -d $ROOT/db ]; then
  mkdir $ROOT/db
fi

$ROOT/scripts/install-python.sh  || exit 1
$ROOT/scripts/install-software-frommirror.sh || exit 1
$ROOT/scripts/write-config.sh || exit 1

source $ROOT/venv/bin/activate
export LD_LIBRARY_PATH=$ROOT/venv/local/lib:$ROOT/venv/lib

if [ ! -e $ROOT/db/app.db ]; then python $ROOT/db_create.py; fi
 