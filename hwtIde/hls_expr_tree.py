from flask.blueprints import Blueprint
from flask.templating import render_template


hlsExprTreeBp = Blueprint('hlsExprTree',
                          __name__,
                          template_folder='templates/hls/expr_tree/')


@hlsExprTreeBp.route('/expr-tree-test/')
def expr_tree_test():
    return render_template('expr_tree.html')
