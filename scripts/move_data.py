import re
import os
import sys

ROOT = os.environ.get('ROOT')
sys.path.append(ROOT)

from app import app, db
from app.models import LanguageModel, Corpus, MonolingualCorpus, Bitext, Translator

def move_item(model, path_expr, new_path_prefix):
    for item in model.query.all():
        current_path = item.path
        groups = re.match(path_expr, current_path)
        if groups:
            new_path = ROOT + new_path_prefix + groups.group(1)
            item.path = new_path
            db.session.commit()
            print("Path {} is now {}".format(current_path, new_path_prefix), file=sys.stderr)

move_item(LanguageModel, r'^' + ROOT + r'\/lms\/(.*)$', "/data/lms/")
move_item(Corpus, r'^' + ROOT + r'\/uploads\/(.*)$', "/data/uploads/")
move_item(MonolingualCorpus, r'^' + ROOT + r'\/uploads\/(.*)$',  "/data/uploads/")
move_item(Bitext, r'^' + ROOT + r'\/uploads\/(.*)$',  "/data/uploads/")
