from flask.blueprints import Blueprint
from flask.json import jsonify
from flask.templating import render_template
from hwt.synthesizer.interfaceLevel.unit import Unit
from hwt.interfaces.std import VectSignal


hlsExprTreeBp = Blueprint('hlsExprTree',
                          __name__,
                          template_folder='templates/hls/expr_tree/')


@hlsExprTreeBp.route('/expr-tree-test/')
def expr_tree_test():
    return render_template('expr_tree.html')


class ExampleUnit(Unit):
    def _declr(self):
        self.a = VectSignal(32)
        self.b = VectSignal(32)
        self.c = VectSignal(32)
        self.d = VectSignal(32)

        self.e = VectSignal(32)

    def _impl(self):
        e = (self.a + self.b) * (self.c + self.d)
        self.e(e)


@hlsExprTreeBp.route("/expr-tree-data/", methods=["POST", 'GET'])
def expr_tree_data():
    # if not request.json:
    #    abort(400)
    # query = request.json
    # print(query)

    nodes = [
        {"id": 0, "label": "input a[0]", "level": 0},
        {"id": 1, "label": "input a[1]", "level": 0},
        {"id": 2, "label": "input a[2]", "level": 0},
        {"id": 3, "label": "input a[3]", "level": 0},

        {"id": 4, "label": "*", "level": 1},
        {"id": 5, "label": "*", "level": 1},
        {"id": 6, "label": "+", "level": 2},
        {"id": 7, "label": "output[0]", "level": 3},
        {"id": 8, "label": "-", "level": 2},
        {"id": 9, "label": "output[1]", "level": 3},
    ]

    edges = [
        {"id": 0, "source": 0, "target": 4},
        {"id": 1, "source": 1, "target": 4},
        {"id": 2, "source": 2, "target": 5},
        {"id": 3, "source": 3, "target": 5},

        {"id": 4, "source": 4, "target": 6},
        {"id": 5, "source": 5, "target": 6},
        {"id": 6, "source": 6, "target": 7},

        {"id": 7, "source": 4, "target": 8},
        {"id": 8, "source": 5, "target": 8},
        {"id": 9, "source": 8, "target": 9}
    ]
    data = {
        "nodes": nodes,
        "edges": edges,
    }
    return jsonify(data)
