from datetime import datetime
from time import time
from traceback import print_stack

import kombu.five
from app import db
from app.models import LanguageModel, TranslatorFromBitext, User
from app.utils import tasks as celerytasks
from app.utils import user_utils, utils
from flask import Blueprint, abort, jsonify, render_template, request
from flask_babel import _
from flask_login import current_user, login_required

from celery.result import AsyncResult
import os
import signal

dashboard_blueprint = Blueprint('dashboard', __name__, template_folder='templates')

@dashboard_blueprint.route('/dashboard')
@utils.condec(login_required, user_utils.isUserLoginEnabled())
def dashboard():
  u = user_utils.get_user()
  if u == None or u.admin:
    return render_template("dashboard.html", title = _("Dashboard"), user = u)
  else:
    return redirect("/")

@dashboard_blueprint.route('/actions/mt-list', methods=["POST"])
@utils.condec(login_required, user_utils.isUserLoginEnabled())
def mt_list():
  columns = [None, TranslatorFromBitext.name, TranslatorFromBitext.lang1, TranslatorFromBitext.size_mb, TranslatorFromBitext.mydate, User.email]

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
    search_str = '%{0}%'.format(search)
    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="ml-checkbox-{0}"/></div>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'

    data = [[checkbox.format(t.id), t.name, t.lang1+"-"+t.lang2, t.size_mb, t.mydate.strftime(date_fmt) if t.mydate else '', t.get_user().email, ""]
            for t in db.session.query(TranslatorFromBitext).join(User, User.id == TranslatorFromBitext.user_id).filter(TranslatorFromBitext.name.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
    
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = User.query.count(),
                   recordsFiltered = User.query.filter(User.username.like(search_str)).count())

  except ValueError:
    abort(401)
    return

@dashboard_blueprint.route('/actions/user-list', methods=["POST"])
@utils.condec(login_required, user_utils.isUserLoginEnabled())
def user_list():
  columns = [None, User.username, User.email, None, None, User.admin, User.banned]

  try:
    start     = int(request.form['start'])
    length    = int(request.form['length'])
    draw      = int(request.form['draw'])
    order_col = int(request.form['order[0][column]'])

    order_dir = request.form['order[0][dir]']
    if order_dir not in ['asc', 'desc']:
      raise ValueError('order[0][dir] must be "asc" or "desc"')

    search     = request.form['search[value]']
    search_str = '%{0}%'.format(search)

    checkbox   = '<span class="checkbox"><input class="file_checkbox" type="checkbox" id="ul-checkbox-{0}"/></div>'
    toggle = '<button type="button" id="button-toggle-{0}" class="btn btn-default btn-sm">'+_('Toggle')+'</button>'
    date_fmt   = '%Y-%m-%d %H:%M:%S'


    data = [[checkbox.format(u.id), u.username, u.email, u.n_engines(), u.size_mb(), u.admin, u.banned, toggle.format(u.id) if u.id != current_user.id else ""]
            for u in User.query.filter(User.username.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = User.query.count(),
                   recordsFiltered = User.query.filter(User.username.like(search_str)).count())

  except ValueError:
    abort(401)
    return


@dashboard_blueprint.route('/actions/queue-list', methods=["POST"])
def queue_list():
  draw      = int(request.form['draw'])

  workers = celerytasks.celery.control.inspect().stats().keys()
  if len(workers) > 0:
    worker_name = list(workers)[0]
    inspector = celerytasks.celery.control.inspect([worker_name])

    tasks = {
      "active": inspector.active()[worker_name],
      "reserved": inspector.reserved()[worker_name],
      "scheduled": inspector.scheduled()[worker_name]
    }

    data = []
    for status in tasks.keys():
      for task in tasks[status]:
        print(task)
        start_utc = datetime.fromtimestamp(time() - kombu.five.monotonic() + task['time_start']).strftime("%Y-%m-%d %H:%M:%S")

        item = None
        if task['type'] == 'app.utils.tasks.train_smt':
          item = TranslatorFromBitext.query.filter(TranslatorFromBitext.task_id.like(task['id'])).first()
        elif task['type'] == 'app.utils.tasks.train_simple_smt':
          item = TranslatorFromBitext.query.filter(TranslatorFromBitext.task_id.like(task['id'])).first()
        elif task['type'] == 'app.utils.tasks.train_lm':
          item = LanguageModel.query.filter(LanguageModel.task_id.like(task['id'])).first()
        else:
          continue

        data.append([
          task['id'],
          task['name'],
          status,
          start_utc,
          worker_name,
          item.name if item else ''
        ])
    
    return jsonify(draw = (draw + 1), data = data, recordsTotal = len(data), recordsFiltered = len(data))
  else:
    return jsonify(["error"])

@dashboard_blueprint.route('/actions/revoke-task', methods=["POST"])
def terminate_task():
  task_id = request.form['task_id']

  try:
    task = AsyncResult(task_id, app=celerytasks.celery)
    proc_id = task.info['proc_id']
    os.killpg(proc_id, signal.SIGTERM)
    celerytasks.celery.control.revoke(task_id, terminate=True)
    return jsonify({"result": 200})
  except Exception as e:
    return jsonify({"result": -1})
