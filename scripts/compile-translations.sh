#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
source $ROOT/venv/bin/activate
cd $ROOT/app
pybabel compile -d translations
