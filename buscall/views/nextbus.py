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
def predict_for_stop(route_id, stop_id, format="html"):
    prediction = nextbus.get_prediction(route_id, stop_id)
    if format.lower() == "twiml":
        return get_twiml(route, stop, prediction)
    else:
        return render_template('routes/predict.html', prediction=prediction)

def get_twiml(route, stop, prediction):
    r = tw.Response()
    r.addSay("%s minutes until %s bus arrives at %s, heading towards %s.")
    return r