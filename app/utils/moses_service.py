from app import app

import os
import subprocess


def moses_start(engine, port = app.config["MOSES_SERVICE_PORT"]):
  command = "{} {} {} {}".format(os.path.join(app.config["SCRIPTS_FOLDER"], "moses_server_startup.sh"), 
                                 engine, port, app.config["MOSES_SERVICE_PIDFILE"])
  proc = subprocess.Popen(command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();

def moses_stop():
  command = "{} {}".format(os.path.join(app.config["SCRIPTS_FOLDER"], "moses_server_shutdown.sh"), app.config["MOSES_SERVICE_PIDFILE"])
  proc = subprocess.Popen(command, shell = True, preexec_fn = os.setsid, close_fds = True)
  proc.communicate();
