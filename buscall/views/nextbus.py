from buscall import app
from flask import render_template, Response
from buscall.models import nextbus
from buscall.models.twilio import get_twiml
import simplejson_mod as json
from buscall.models.nextbus import AGENCIES
try:
    from collections import OrderedDict
except ImportError:
    from collections_backport import OrderedDict

def render_json(obj):
    if isinstance(obj, OrderedDict):
        obj["_order"] = obj.keys()
    return Response(json.dumps(obj, use_decimal=True), mimetype="application/json")

@app.route('/<agency_id>')
@app.route('/<agency_id>.<format>')
def show_agency(agency_id, format="html"):
    agency = AGENCIES[agency_id]
    if format.lower() == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/<agency_id>/routes')
@app.route('/<agency_id>/routes.<format>')
def routes_for_agency(agency_id, format="html"):
    agency = AGENCIES[agency_id]
    routes = nextbus.get_routes(agency_id=agency_id)
    if format.lower() == "json":
        return render_json(routes)
    else:
        return render_template('routes/index.html',
            agency=agency, routes=routes)

@app.route('/<agency_id>/routes/<route_id>')
@app.route('/<agency_id>/routes/<route_id>.<format>')
def show_route(agency_id, route_id, format="html"):
    if format.lower() == "json":
        route = nextbus.get_route(agency_id, route_id, use_dicts=True)
        return render_json(route)
    else:
        agency = AGENCIES[agency_id]
        route = nextbus.get_route(agency_id, route_id)
        direction_dict = {}
        for d in route.directions:
            direction_dict[d.id] = d
        stop_dict = {}
        for s in route.stops:
            stop_dict[s.id] = s
    
        return render_template('routes/show.html',
            agency=agency, route=route, 
            directions=direction_dict, stops=stop_dict)

@app.route('/predict/<agency_id>/<route_id>/<direction_id>/<stop_id>')
@app.route('/predict/<agency_id>/<route_id>/<direction_id>/<stop_id>.<format>')
@app.route('/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predict')
@app.route('/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predict.<format>')
def predict_for_stop(agency_id, route_id, direction_id, stop_id, format="html"):
    prediction = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
    if format.lower() == "twiml":
        twiml = get_twiml(prediction)
        return Response(twiml, mimetype="text/xml")
    elif format.lower() == "json":
        return render_json(prediction)
    else:
        return render_template('routes/predict.html', prediction=prediction)