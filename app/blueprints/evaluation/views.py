from app.utils import user_utils, metrics
from flask import Blueprint, render_template, request, jsonify
from flask_babel import _

import tempfile
import os

evaluation_blueprint = Blueprint('evaluation', __name__, template_folder='templates')

@evaluation_blueprint.route('/evaluate')
def evaluate():
  return render_template("evaluate.html", title = _("Evaluate"), user = user_utils.get_user())

@evaluation_blueprint.route('/actions/perform-evaluation', methods = ["POST"])
def perform_evaluation():
    reftemp = tempfile.NamedTemporaryFile(delete=False)
    reffile = request.files["htrans"]
    reforig = request.files["htrans"].filename
    refname = reftemp.name
    
    for i in reffile:
        reftemp.write(i)
    reftemp.close()

    records = []
    
    for mt in request.files.getlist("mt[]"):
        mttemp = tempfile.NamedTemporaryFile(delete=False)
        mtorig = mt.filename
        mtname = mttemp.name
        for i in mt:
            mttemp.write(i)
        mttemp.close()
        n1 = tempfile.NamedTemporaryFile(delete=False)
        n2 = tempfile.NamedTemporaryFile(delete=False)
        l1 = n1.name
        l2 = n2.name
        n1.close()
        n2.close()
        metrics.prepare_files(refname, mtname, l1, l2)
        
        try:
            records.append({"name": mtorig,
                            "bleu": metrics.bleu(l1,l2), 
                            "ter": metrics.ter(l1,l2), 
                            "wer": metrics.wer(l1,l2), 
                            "chrf3":metrics.chrF3(l1,l2),
                            "beer":metrics.beer(l1,l2)})
        except:
            return jsonify({"error":_("Invalid input files")})
        os.unlink(l1)
        os.unlink(l2)
        os.unlink(mtname)
        
    os.unlink(refname)

    return jsonify({"records":records})
