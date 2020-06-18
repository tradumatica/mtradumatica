#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
declare -a FOLDERS=("db" "lms" "logs" "proc" "redis-data" "tmp" "translators" "uploads")

for folder in $FOLDERS
do
    mv $folder data/$folder
done

cd $ROOT
source venv/bin/activate
ROOT=$ROOT python3 scripts/move_data.py
