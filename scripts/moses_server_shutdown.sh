ROOT=$(readlink -f $(dirname $(readlink -f $0))/..)

source $ROOT/venv/bin/activate

if [ -f "$ROOT/proc/moses_server.pid" ]; then
  curpid=$(cat "$ROOT/proc/moses_server.pid")
  kill -9 $curpid
  rm "$ROOT/proc/moses_server.pid"
fi





