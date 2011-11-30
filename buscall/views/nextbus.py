from buscall import app
from flask import render_template, request, Response, abort, g
from buscall.models import nextbus
from buscall.models.nextbus import NextbusError
from buscall.models.twilio import get_twiml
import simplejson as json
from buscall.models.nextbus import get_agency, get_route, get_direction, get_stop
try:
    from collections import OrderedDict
except ImportError:
    from collections_backport import OrderedDict

def render_json(obj):
    if isinstance(obj, OrderedDict):
        obj["_order"] = obj.keys()
    return Response(json.dumps(obj, use_decimal=True), mimetype="application/json")

@app.route('/<agency_id>')
def show_agency(agency_id):
    agency = get_agency(agency_id)
    if g.request_format == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/<agency_id>/routes')
def routes_for_agency(agency_id):
    agency = get_agency(agency_id)
    routes = [get_route(agency_id, route_id) for route_id in agency.route_ids]
    if g.request_format == "json":
        return render_json(routes)
    else:
        return render_template('routes/index.html',
            agency=agency, routes=routes)

@app.route('/<agency_id>/routes/<route_id>')
def show_route(agency_id, route_id):
    route = nextbus.get_route(agency_id, route_id)
    if g.request_format == "json":
        return render_json(route)
    else:
        context = dict(
            agency = nextbus.get_agency(agency_id),
            route = route,
            directions = [nextbus.get_direction(agency_id, route_id, direction_id) for direction_id in route.direction_ids],
        )
        return render_template('routes/show.html', **context)

@app.route('/<agency_id>/routes/<route_id>/directions/<direction_id>')
def show_direction(agency_id, route_id, direction_id):
    direction = nextbus.get_direction(agency_id, route_id, direction_id)
    if g.request_format == "json":
        return render_json(direction)
    else:
        context = dict(
            agency = nextbus.get_agency(agency_id),
            route = nextbus.get_route(agency_id, route_id),
            direction = direction,
            stops = [nextbus.get_stop(agency_id, route_id, direction_id, stop_id) for stop_id in direction.stop_ids],
        )
        return render_template('directions/show.html', **context)

@app.route('/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>')
def show_stop(agency_id, route_id, direction_id, stop_id):
    stop = nextbus.get_stop(agency_id, route_id, direction_id, stop_id)
    if g.request_format == "json":
        return render_json(stop)
    else:
        context = dict(
            agency = nextbus.get_agency(agency_id),
            route = nextbus.get_route(agency_id, route_id),
            direction = nextbus.get_direction(agency_id, route_id, direction_id),
            stop = stop,
            predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id),
        )
        return render_template('stops/show.html', **context)

@app.route('/predictions/<agency_id>/<route_id>/<direction_id>/<stop_id>')
@app.route('/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions')
def predict_for_stop(agency_id, route_id, direction_id, stop_id):
    predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
    if g.request_format == "twiml":
        twiml = get_twiml(predictions)
        return Response(twiml, mimetype="text/xml")
    else:
        return render_json(predictions)

