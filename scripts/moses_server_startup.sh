#!/bin/bash

export LC_ALL=C.UTF-8
ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)
ENGINE="$1"
PORT="$2"
PIDFILE="$3"

source $ROOT/venv/bin/activate

MOSES_INI="moses.ini"
if [ -f "$ROOT/translators/$ENGINE/moses.tuned.ini" ]; then
  MOSES_INI="moses.tuned.ini"
fi

if [ -f "$PIDFILE" ]; then
  curpid=$(cat "$PIDFILE")
  kill -9 $curpid
  rm "$PIDFILE"
fi

[ -d $ROOT/logs ] || mkdir $ROOT/logs

cd $ROOT/translators/$ENGINE
nohup mosesserver --server-port $PORT -f $MOSES_INI &>>$ROOT/logs/moses_server.log &
echo $! >"$PIDFILE"