from buscall import app
from flask import render_template, Response
from buscall.models import nextbus, twilio
import simplejson as json
from buscall.models.nextbus import AGENCIES
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

def render_json(obj):
    if isinstance(obj, OrderedDict):
        obj["_order"] = obj.keys()
    return Response(json.dumps(obj, use_decimal=True), mimetype="application/json")

@app.route('/<agency_id>')
@app.route('/<agency_id>.<format>')
def show_agency(agency_id, format="html"):
    #routes = nextbus.get_routes(agency_id=agency_id)
    agency = {"id": agency_id, "name": AGENCIES[agency_id]}
    if format.lower() == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/<agency_id>/routes')
@app.route('/<agency_id>/routes.<format>')
def routes_for_agency(agency_id, format="html"):
    routes = nextbus.get_routes(agency_id=agency_id)
    if format.lower() == "json":
        return render_json(routes)
    else:
        return render_template('routes/index.html',
            agency_id=agency_id, routes=routes)

@app.route('/<agency_id>/routes/<route_id>')
@app.route('/<agency_id>/routes/<route_id>.<format>')
def show_route(agency_id, route_id, format="html"):
    route = nextbus.get_route(agency_id, route_id)
    directions = nextbus.get_route_directions(route)
    if format.lower() == "json":
        return render_json(route)
    else:
        return render_template('routes/show.html',
            agency_id=agency_id, route=route, directions=directions)

@app.route('/predict/<agency_id>/<route_id>/<stop_id>')
@app.route('/predict/<agency_id>/<route_id>/<stop_id>.<format>')
def predict_for_stop(agency_id, route_id, stop_id, format="html"):
    prediction = nextbus.get_prediction(agency_id, route_id, stop_id)
    if format.lower() == "twiml":
        twiml = twilio.get_twiml(prediction)
        return Response(twiml, mimetype="text/xml")
    elif format.lower() == "json":
        return render_json(prediction)
    else:
        return render_template('routes/predict.html', prediction=prediction)