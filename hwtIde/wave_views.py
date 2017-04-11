from flask.blueprints import Blueprint
from flask.templating import render_template
from flask import abort, jsonify, request
from hwt.bitmask import mask

waveBp = Blueprint('wave',
                   __name__,
                   template_folder='templates/wave/')


@waveBp.route('/wave-test/')
def connections_test():
    return render_template('wave_test.html')


@waveBp.route("/wave-data/", methods=["POST"])
def wave_data():
    if not request.json:
        abort(400)
    query = request.json
    print(query)


    data = [["signal0", {"name": "bits",
                         "width": 16},
             [(i, (i, mask(16))) for i in range(16)]],
            ]

    return jsonify(data)