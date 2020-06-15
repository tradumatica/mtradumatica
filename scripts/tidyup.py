#!python3
import sys
import os
import shutil

# Check params

if len(sys.argv) < 2:
    print("App root must be specified", file=sys.stderr)
    sys.exit(1)

ROOT = sys.argv[1]

sys.path.append(ROOT)

# Ready to roll

from app import app, db
from app.models import OAuth, User
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
fh = logging.FileHandler(os.path.join(app.config['DATA_FOLDER'], 'logs/tidyup.log'), 'a')
fh.setFormatter(logging.Formatter('%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(fh)

try:
    TIME_LIMIT_DAYS = int(app.config['TIME_LIMIT_DAYS'])
except ValueError:
    logger.error("Time limit is not valid")
    sys.exit(1)

logger.info("Running with {} days".format(TIME_LIMIT_DAYS))

if TIME_LIMIT_DAYS == 0:
    logger.error("User data time limit set to 0")
    sys.exit()

TIME_LIMIT_SECONDS = TIME_LIMIT_DAYS * 24 * 3600
now = datetime.utcnow()

def remove_item(path):
    if not os.path.exists(path):
        return False

    try:
        if os.path.isdir(path):
            shutil.rmtree(path)
        else:
            os.remove(path)
    except Exception as e:
        logger.error(e)
        return False

    return True

for oauth in OAuth.query.all():
    if oauth.created_at is not None:
        time_diff = (now - oauth.created_at).total_seconds()
        if time_diff >= TIME_LIMIT_SECONDS:
            user = User.query.filter_by(id=oauth.user_id).first()
            logger.info("[USER] {}".format(user.email))

            items_to_delete = []

            try:
                for corpus in user.corpora:
                    items_to_delete.append(corpus)
                    remove_item(corpus.path)
                    logger.info("[PATH] {}".format(corpus.path))

                for translator in user.tfbitexts:
                    items_to_delete.append(translator)
                    for path in translator.get_path():
                        remove_item(path)
                        logger.info("[PATH] {}".format(path))

                for translator in user.translators:
                    items_to_delete.append(translator)
                    remove_item(translator.path)
                    logger.info("[PATH] {}".format(translator.path))
                
                for model in user.language_models:
                    items_to_delete.append(model)
                    remove_item(model.path)
                    logger.info("[PATH] {}".format(model.path))

                for bitext in user.bitexts:
                    items_to_delete.append(bitext)
                    remove_item(bitext.path)
                    logger.info("[PATH] {}".format(bitext.path))

                for monotext in user.mono_corpora:
                    items_to_delete.append(monotext)
                    remove_item(monotext.path)
                    logger.info("[PATH] {}".format(monotext.path))

                for translation in user.translation:
                    items_to_delete.append(translation)
                    remove_item(translation.path)
                    logger.info("[PATH] {}".format(translation.path))

                # Delete from DB
                for item in items_to_delete:
                    db.session.delete(item)

                db.session.delete(user)
                db.session.delete(oauth)

                db.session.commit()
            except:
                logger.error("Error while deleting items for user #{} ({})".format(user.id, user.email))
                sys.exit(1)
                