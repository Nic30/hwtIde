from flask import Flask, render_template
from flask.helpers import send_from_directory

from hwtIde.dependencyViews import dependenciesBp
from hwtIde.hls_connections_views import connectionsBp
from hwtIde.wave_views import waveBp


app = Flask("hwtIde")


# for loading all static files (antipatent, but it is necessary because
# app is not deployed on webserver0
@app.route('/static/<path:path>')
def send_static(path):
    return send_from_directory('static', path)


@app.route('/')
def index():
    return render_template('index.html')


# http://roberto.open-lab.com/2012/06/14/the-javascript-gantt-odyssey/
@app.route('/gantt/')
def gantt():
    return render_template('hls/gantt_chart.html', ganttTasks=[], ganttTaskNames=[])


app.register_blueprint(connectionsBp)
app.register_blueprint(dependenciesBp)
app.register_blueprint(waveBp)

if __name__ == '__main__':
    app.run(debug=True)
    # app.run(host='0.0.0.0')
