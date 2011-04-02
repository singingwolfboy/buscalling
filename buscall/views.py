from buscall import app
from flask import render_template
from buscall.models import nextbus

@app.route('/')
def hello():
    return render_template('hello.html')

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"

@app.route('/routes')
def index_routes():
    routes = nextbus.get_all_routes()
    return render_template('routes/index.html', routes=routes)

@app.route('/routes/<route_id>')
def show_route(route_id):
    route = nextbus.get_route(route_id)
    directions = nextbus.get_route_directions(route)
    return render_template('routes/show.html', route=route, directions=directions)

@app.route('/predict/<route_id>/<stop_id>')
@app.route('/predict/<route_id>/<stop_id>/<dir_id>')
def predict_for_stop(route_id, stop_id, dir_id=None):
    route = nextbus.get_route(route_id)
    stop = route['stops'][stop_id]
    predictions = nextbus.get_predictions(route_id, stop_id, dir_id)
    return render_template('routes/predict.html', route=route, stop=stop, predictions=predictions)
