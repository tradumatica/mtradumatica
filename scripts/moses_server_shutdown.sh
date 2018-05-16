ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

source $ROOT/venv/bin/activate

PIDFILE="$1"

if [ -f "$PIDFILE" ]; then
  curpid=$(cat "$PIDFILE")
  kill -9 $curpid
  rm "$PIDFILE"
fi





