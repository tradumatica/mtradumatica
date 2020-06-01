#!/bin/bash 
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

$ROOT/scripts/startup.sh

[ -d $ROOT/data/logs ] || mkdir $ROOT/data/logs

touch $ROOT/data/logs/celery-worker.log $ROOT/data/logs/errors.log $ROOT/data/logs/redis.log
tail -f $ROOT/data/logs/celery-worker.log $ROOT/data/logs/errors.log $ROOT/data/logs/redis.log
