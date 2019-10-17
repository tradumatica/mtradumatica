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

if [ ! -d $ROOT/db ]
then mkdir $ROOT/db
fi

if [ ! -d $ROOT/proc ]
then mkdir $ROOT/proc
fi

if [ ! -d $ROOT/logs ]
then mkdir $ROOT/logs
fi

if [ ! -d $ROOT/uploads ]
then mkdir $ROOT/uploads
fi

if [ ! -d $ROOT/translators ]
then mkdir $ROOT/translators
fi

if [ ! -d $ROOT/tmp ]
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

if [ ! -d $ROOT/redis-data ]
then mkdir $ROOT/redis-data
fi

redis-server $ROOT/conf/redis.conf # as a daemon, with pidfile
sleep 2
nohup celery worker --workdir $ROOT \
                    -A app.utils.tasks.celery --loglevel=info \
                    --logfile=$ROOT/logs/celery-worker.log &

echo $! >$ROOT/proc/celery.pid

if [ "$DEBUG_MODE" != "1" ]
then nohup gunicorn -c $ROOT/conf/gunicorn.conf app:app &
fi
