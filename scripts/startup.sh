#!/bin/bash

export LC_ALL=C.UTF-8
DEBUG_MODE=0
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
OPTION=$1

# Required in docker - root environments
export C_FORCE_ROOT="true"

if [ ! -e $ROOT/venv/bin/activate ]
then echo "Installation failed, please re-install"
     exit
fi

if [ ! -d $ROOT/data/db ]
then mkdir $ROOT/data/db
fi

if [ ! -d $ROOT/data/proc ]
then mkdir $ROOT/data/proc
fi

if [ ! -d $ROOT/data/logs ]
then mkdir $ROOT/data/logs
fi

if [ ! -d $ROOT/data/uploads ]
then mkdir $ROOT/data/uploads
fi

if [ ! -d $ROOT/data/translators ]
then mkdir $ROOT/data/translators
fi

if [ ! -d $ROOT/data/tmp ]
then mkdir $ROOT/tmp
fi

if [ "$OPTION" = "-d" ]
  then DEBUG_MODE="1"
       echo "[debug] starting redis + celery only... [done]"
  else echo "Starting redis + celery + gunicorn... [done]"
fi

exec 1>/dev/null
exec 2>/dev/null

$ROOT/scripts/shutdown.sh >/dev/null

source $ROOT/venv/bin/activate

if [ ! -d $ROOT/data/redis-data ]
then mkdir $ROOT/data/redis-data
fi

redis-server $ROOT/conf/redis.conf # as a daemon, with pidfile
sleep 2
nohup celery worker --workdir $ROOT \
                    -A app.utils.tasks.celery --loglevel=info \
                    --logfile=$ROOT/data/logs/celery-worker.log &

echo $! >$ROOT/data/proc/celery.pid

if [ "$DEBUG_MODE" != "1" ]
then nohup gunicorn -c $ROOT/conf/gunicorn.conf app:app &
fi
