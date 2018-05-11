import os
basedir = os.path.abspath(os.path.dirname(__file__))

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

TRANSLATION_PROGRAM   = os.path.join(SCRIPTS_FOLDER, "translate-docs.sh")
TRANSLATION_PROGRAM_TRACE = os.path.join(SCRIPTS_FOLDER, "translate-trace.sh")
QUERY_LM_PROGRAM      = os.path.join(EXECUTABLE_FOLDER, "query")
QUERY_TM_PROGRAM      = os.path.join(EXECUTABLE_FOLDER, "queryPhraseTableMin")
CELERY_BROKER_URL     = 'redis://localhost:6379/0'
CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'
CELERYD_CONCURRENCY   = 4


SECRET_KEY = 'development key' # change by your own
DEBUG      = True

USER_LOGIN_ENABLED          = True
ENABLE_NEW_LOGINS           = True
ADMINS                      = ['sergio.ortiz@gmail.com']
BANNED_USERS                = []
OAUTHLIB_INSECURE_TRANSPORT = True # True also behind firewall,  False -> require HTTPS
GOOGLE_OAUTH_CLIENT_ID      = '629052210385-6vvkbbkn744lst4sg0s1l765424r3a66.apps.googleusercontent.com'
GOOGLE_OAUTH_CLIENT_SECRET  = 'dztt2KCtqlTfowlTULSzdfpE'

