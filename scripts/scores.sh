#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

source $ROOT/venv/bin/activate
python $ROOT/app/metrics.py $1 $2

