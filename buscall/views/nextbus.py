from buscall import app
from flask import render_template, Response, g
from buscall.models import nextbus
from buscall.models.twilio import get_twiml
import simplejson as json
from buscall.models.nextbus import get_agencies, get_agency, get_route, get_direction, get_stop

__all__ = ['agency_list', 'agency_detail', 'route_list', 'route_detail',
        'direction_list', 'direction_detail', 'stop_list', 'stop_detail',
        'prediction_list']

def render_json(obj, count=None):
    resp = Response(json.dumps(obj, use_decimal=True), mimetype="application/json")
    if count is not None:
        if g.limit:
            resp.headers.add("X-Limit", g.limit)
        resp.headers.add("X-Offset", g.offset)
        resp.headers.add("X-TotalCount", count)
    return resp

@app.route('/agencies')
def agency_list():
    agencies = get_agencies()
    if g.request_format == "json":
        if g.limit:
            page = agencies[g.offset:g.offset+g.limit]
        else:
            page = agencies[g.offset:]
        return render_json(page)
    else:
        return render_template('agencies/index.html', agencies=agencies)

@app.route('/agencies/<agency_id>')
def agency_detail(agency_id):
    agency = get_agency(agency_id)
    if g.request_format == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/agencies/<agency_id>/routes')
def route_list(agency_id):
    agency = get_agency(agency_id)
    count = len(agency.route_ids)
    if g.request_format == "json":
        if g.limit:
            page = agency.route_ids[g.offset:g.offset+g.limit]
        else:
            page = agency.route_ids[g.offset:]
        routes = [get_route(agency_id, route_id) for route_id in page]
        return render_json(routes, count)
    else:
        routes = [get_route(agency_id, route_id) for route_id in agency.route_ids]
        return render_template('routes/index.html',
            agency=agency, routes=routes, count=count)

@app.route('/agencies/<agency_id>/routes/<route_id>')
def route_detail(agency_id, route_id):
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

@app.route('/agencies/<agency_id>/routes/<route_id>/directions')
def direction_list(agency_id, route_id):
    route = get_route(agency_id, route_id)
    count = len(route.direction_ids)
    if g.request_format == "json":
        if g.limit:
            page = route.direction_ids[g.offset:g.offset+g.limit]
        else:
            page = route.direction_ids[g.offset:]
        directions = [get_direction(agency_id, route_id, direction_id) for direction_id in page]
        return render_json(directions, count)
    else:
        agency = get_agency(agency_id)
        directions = [get_direction(agency_id, route_id, direction_id) for direction_id in route.direction_ids]
        return render_template('routes/index.html',
            agency=agency, route=route, directions=directions, count=count)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>')
def direction_detail(agency_id, route_id, direction_id):
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

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops')
def stop_list(agency_id, route_id, direction_id, stop_id):
    direction = get_direction(agency_id, route_id, direction_id)
    count = len(direction.stop_ids)
    if g.request_format == "json":
        if g.limit:
            page = direction.stop_ids[g.offset:g.offset+g.limit]
        else:
            page = direction.stop_ids[g.offset:]
        stops = [get_stop(agency_id, route_id, direction_id, stop_id) for stop_id in page]
        return render_json(stops, count)
    else:
        agency = get_agency(agency_id)
        route = get_route(agency_id, route_id)
        stops = [get_stop(agency_id, route_id, direction_id, stop_id) for stop_id in direction.stop_ids]
        return render_template('routes/index.html',
            agency=agency, route=route, direction=direction, stops=stops, count=count)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>')
def stop_detail(agency_id, route_id, direction_id, stop_id):
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
@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions')
def prediction_list(agency_id, route_id, direction_id, stop_id):
    predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
    if g.request_format == "twiml":
        twiml = get_twiml(predictions)
        return Response(twiml, mimetype="text/xml")
    else:
        return render_json(predictions)

