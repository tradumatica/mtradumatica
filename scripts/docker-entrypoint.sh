#!/bin/bash 
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

$ROOT/scripts/startup.sh

[ -d $ROOT/logs ] || mkdir $ROOT/logs

touch $ROOT/logs/celery-worker.log $ROOT/logs/errors.log $ROOT/logs/redis.log
tail -f $ROOT/logs/celery-worker.log $ROOT/logs/errors.log $ROOT/logs/redis.log
