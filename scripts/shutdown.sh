#!/bin/bash

ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

source $ROOT/venv/bin/activate

for i in $(find $ROOT/data/proc -type f -name "*.pid");
do
  curpid=$(cat $i)
  for j in $(pgrep -P $curpid);
  do 
    kill -9 $j
  done
  kill -9 $curpid
  rm $i
done






