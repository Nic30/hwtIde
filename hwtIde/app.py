from flask import Flask, render_template
from flask.helpers import send_from_directory

from hwtIde.dependencyViews import dependenciesBp
from hwtIde.hls_connections_views import connectionsBp
from hwtIde.hls_expr_tree import hlsExprTreeBp
from hwtIde.moduleWalking import walk_Unit_cls_in_module
from hwtIde.wave_views import waveBp
import hwtLib


app = Flask("hwtIde")


# for loading all static files (antipatent, but it is necessary because
# app is not deployed on webserver
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    return render_template('index.html',
                           unitClasses=sorted(
                               list(walk_Unit_cls_in_module(hwtLib)),
                               key=lambda u: u.__name__)
                           )


# http://roberto.open-lab.com/2012/06/14/the-javascript-gantt-odyssey/
@app.route('/gantt/')
def gantt():
    return render_template('hls/gantt_chart.html',
                           ganttTasks=[], ganttTaskNames=[])


app.register_blueprint(connectionsBp)
app.register_blueprint(dependenciesBp)
app.register_blueprint(waveBp)
app.register_blueprint(hlsExprTreeBp)


if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0')
