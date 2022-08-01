# -*- coding: utf-8 -*-

import os
basedir = os.path.abspath(os.path.dirname(__file__))

BASEDIR = basedir
DATA_FOLDER           = os.path.join(basedir, "data")
UPLOAD_FOLDER         = os.path.join(DATA_FOLDER, "uploads")
DOWNLOAD_FOLDER       = os.path.join(basedir, "downloads")
TRANSLATORS_FOLDER    = os.path.join(DATA_FOLDER, "translators")
LMS_FOLDER            = os.path.join(DATA_FOLDER, "lms")
SCRIPTS_FOLDER        = os.path.join(basedir, "scripts")
TMP_FOLDER            = os.path.join(DATA_FOLDER, "tmp")
EXECUTABLE_FOLDER     = os.path.join(os.path.join(basedir, "venv"), "bin")
PROC_FOLDER           = os.path.join(DATA_FOLDER, "proc")
TRANSLATION_PROGRAM   = os.path.join(SCRIPTS_FOLDER, "translate-docs.sh")
TRANSLATION_PROGRAM_TRACE = os.path.join(SCRIPTS_FOLDER, "translate-trace.sh")
REBUNDLE_PROGRAM      = os.path.join(SCRIPTS_FOLDER, "rebundle.sh")
QUERY_LM_PROGRAM      = os.path.join(EXECUTABLE_FOLDER, "query")
QUERY_TM_PROGRAM      = os.path.join(SCRIPTS_FOLDER, "query_phrase_table.sh")
TMX_UNFORMAT_SCRIPT   = os.path.join(SCRIPTS_FOLDER, "tmx-unformat.py")
TMX_REFORMAT_SCRIPT   = os.path.join(SCRIPTS_FOLDER, "tmx-reformat.py")

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(DATA_FOLDER, 'db', 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')
SQLALCHEMY_TRACK_MODIFICATIONS = False
#MAX_CONTENT_LENGTH = 1024# * 1024 * 1024 # 1 GB BY DEFAULT INF

CELERY_BROKER_URL     = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERYD_CONCURRENCY   = 4
MOSES_SERVICE_PORT    = 10000
MOSES_SERVICE_PIDFILE = os.path.join(PROC_FOLDER, "moses_server.pid")

SECRET_KEY = 'development key' # change by your own
DEBUG      = False

# Uncomment it to enable translations. Follow instructions in README.md to add more languages
LANGUAGES = { 'ca': 'Català', 'en': 'English', 'es': 'Spanish' }

USER_LOGIN_ENABLED          = False
ENABLE_NEW_LOGINS           = True
ADMINS                      = ['']
BANNED_USERS                = []
OAUTHLIB_INSECURE_TRANSPORT = True # True also behind firewall,  False -> require HTTPS
GOOGLE_OAUTH_CLIENT_ID      = ''
GOOGLE_OAUTH_CLIENT_SECRET  = ''
GOOGLE_USER_DATA_URL        = '/oauth2/v1/userinfo'
USE_PROXY_FIX               = True 

# Delete users and their associated data if they have not logged in 
# in TIME_LIMIT_DAYS days (must be an integer)
# 0 means no limits
TIME_LIMIT_DAYS = 0

# Count words on upload
WORD_COUNT_ON_UPLOAD = True
WORD_COUNT_UNIQUE_ON_UPLOAD = True
