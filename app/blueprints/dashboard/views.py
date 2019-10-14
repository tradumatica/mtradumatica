from app import db
from app.utils import utils, user_utils
from app.models import TranslatorFromBitext, User

from flask import Blueprint, abort, render_template, request, jsonify
from flask_login import login_required, current_user
from flask_babel import _
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


    data = [[checkbox.format(t.id), t.name, t.lang1+"-"+t.lang2, t.size_mb, t.mydate.strftime(date_fmt), t.get_user().email, ""]
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
    search_str = u'%{0}%'.format(search)

    checkbox   = u'<span class="checkbox"><input class="file_checkbox" type="checkbox" id="ul-checkbox-{0}"/></div>'
    toggle = u'<button type="button" id="button-toggle-{0}" class="btn btn-default btn-sm">'+_('Toggle')+'</button>'
    date_fmt   = u'%Y-%m-%d %H:%M:%S'


    data = [[checkbox.format(u.id), u.username, u.email, u.n_engines(), u.size_mb(), u.admin, u.banned, toggle.format(u.id) if u.id != current_user.id else ""]
            for u in User.query.filter(User.username.like(search_str)).order_by(utils.query_order(columns[order_col], order_dir))][start:start+length]
    return jsonify(draw            = draw,
                   data            = data,
                   recordsTotal    = User.query.count(),
                   recordsFiltered = User.query.filter(User.username.like(search_str)).count())

  except ValueError:
    abort(401)
    return