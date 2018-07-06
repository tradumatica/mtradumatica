# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

BASEDIR = basedir
SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'db', 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
#MAX_CONTENT_LENGTH = 1024# * 1024 * 1024 # 1 GB BY DEFAULT INF

UPLOAD_FOLDER         = os.path.join(basedir, "uploads")
DOWNLOAD_FOLDER       = os.path.join(basedir, "downloads")
TRANSLATORS_FOLDER    = os.path.join(basedir, "translators")
LMS_FOLDER            = os.path.join(basedir, "lms")
SCRIPTS_FOLDER        = os.path.join(basedir, "scripts")
TMP_FOLDER            = os.path.join(basedir, "tmp")
EXECUTABLE_FOLDER     = os.path.join(os.path.join(basedir, "venv"), "bin")
PROC_FOLDER           = os.path.join(basedir, "proc")
TRANSLATION_PROGRAM   = os.path.join(SCRIPTS_FOLDER, "translate-docs.sh")
TRANSLATION_PROGRAM_TRACE = os.path.join(SCRIPTS_FOLDER, "translate-trace.sh")
QUERY_LM_PROGRAM      = os.path.join(EXECUTABLE_FOLDER, "query")
QUERY_TM_PROGRAM      = os.path.join(EXECUTABLE_FOLDER, "queryPhraseTableMin")
CELERY_BROKER_URL     = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERYD_CONCURRENCY   = 4
MOSES_SERVICE_PORT    = 10000
MOSES_SERVICE_PIDFILE = os.path.join(PROC_FOLDER, "moses_server.pid")

SECRET_KEY = 'development key' # change by your own
DEBUG      = False

# Uncomment it to enable translations. Follow instructions in README.md to add more languages
LANGUAGES = { 'ca': u'Català', 'en': u'English', 'es': u'Spanish' }

USER_LOGIN_ENABLED          = False
ENABLE_NEW_LOGINS           = True
ADMINS                      = []
BANNED_USERS                = []
OAUTHLIB_INSECURE_TRANSPORT = True # True also behind firewall,  False -> require HTTPS
GOOGLE_OAUTH_CLIENT_ID      = ''
GOOGLE_OAUTH_CLIENT_SECRET  = ''

