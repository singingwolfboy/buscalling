from buscall import app
from flask import render_template
from buscall.models import nextbus
import twilio_api as tw

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
@app.route('/predict/<route_id>/<stop_id>.<format>')
@app.route('/predict/<route_id>/<stop_id>/<dir_id>')
@app.route('/predict/<route_id>/<stop_id>/<dir_id>.<format>')
def predict_for_stop(route_id, stop_id, dir_id=None, format="html"):
    route = nextbus.get_route(route_id)
    stop = route['stops'][stop_id]
    predictions = nextbus.get_predictions(route_id, stop_id, dir_id)
    if format.lower() == "twiml":
        # only support one direction for phone calls.
        prediction = predictions[dir_id]
        return get_twiml(route, stop, prediction)
    else:
        return render_template('routes/predict.html', route=route, stop=stop, predictions=predictions)

def get_twiml(route, stop, prediction):
    r = tw.Response()
    r.addSay("%s minutes until %s bus arrives at %s, heading towards %s.")
    return r