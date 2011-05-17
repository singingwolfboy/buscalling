from buscall import app
from flask import render_template, Response
from buscall.models import nextbus, twilio
import simplejson as json

def render_json(obj):
    return Response(json.dumps(obj, use_decimal=True), mimetype="application/json")

@app.route('/routes')
@app.route('/routes.<format>')
def index_routes(format="html"):
    routes = nextbus.get_all_routes()
    if format.lower() == "json":
        return render_json(routes)
    else:
        return render_template('routes/index.html', routes=routes)

@app.route('/routes/<route_id>')
@app.route('/routes/<route_id>.<format>')
def show_route(route_id, format="html"):
    route = nextbus.get_route(route_id)
    directions = nextbus.get_route_directions(route)
    if format.lower() == "json":
        return render_json(directions)
    else:
        return render_template('routes/show.html', route=route, directions=directions)

@app.route('/predict/<route_id>/<stop_id>')
@app.route('/predict/<route_id>/<stop_id>.<format>')
def predict_for_stop(route_id, stop_id, format="html"):
    prediction = nextbus.get_prediction(route_id, stop_id)
    if format.lower() == "twiml":
        twiml = twilio.get_twiml(prediction)
        return Response(twiml, mimetype="text/xml")
    elif format.lower() == "json":
        return render_json(prediction)
    else:
        return render_template('routes/predict.html', prediction=prediction)