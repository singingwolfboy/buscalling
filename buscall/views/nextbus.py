from buscall import app
from flask import render_template, request, Response, g
from buscall.models import nextbus
from buscall.models.twilio import get_twiml
import simplejson as json
from buscall.models.nextbus import get_agencies, get_agencies_count, \
        get_agency, get_route, get_direction, get_stop
from functools import wraps

__all__ = ['agency_list', 'agency_detail', 'route_list', 'route_detail',
        'direction_list', 'direction_detail', 'stop_list', 'stop_detail',
        'prediction_list', 'prediction_detail']

def api_list(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not 'limit' in kwargs:
            limit = request.args.get('limit') or request.headers.get('X-Limit')
            try:
                kwargs['limit'] = int(limit)
            except (ValueError, TypeError):
                kwargs['limit'] = 20
        if kwargs['limit'] < 0:
            kwargs['limit'] = 0

        if not 'offset' in kwargs:
            offset = request.args.get('offset') or request.headers.get('X-Offset')
            try:
                kwargs['offset'] = int(offset)
            except (ValueError, TypeError):
                kwargs['offset'] = 0
        if kwargs['offset'] < 0:
            kwargs['offset'] = 0

        return func(*args, **kwargs)
    return wrapper

def render_json(obj, limit=None, offset=None, count=None):
    # get exclusion list
    exclude = request.args.get('exclude') or request.handlers.get('X-Exclude')
    if exclude:
        exclusions = [e.strip() for e in exclude.split(",")]
    else:
        exclusions = []
    # get dictionar(ies)
    def process(model):
        try:
            ret = model._as_url_dict()
        except AttributeError:
            ret = model
        # remove exclusions
        for exclusion in exclusions:
            if exclusion in ret:
                del ret[exclusion]
        return ret
    if isinstance(obj, (list, tuple)):
        view_obj = [process(o) for o in obj]
        count = count or len(view_obj)
    else:
        view_obj = process(obj)
    # make response
    resp = Response(json.dumps(view_obj, use_decimal=True), mimetype="application/json")
    # include headers
    if limit is not None:
        resp.headers.add("X-Limit", limit)
    if offset is not None:
        resp.headers.add("X-Offset", offset)
    if count is not None:
        resp.headers.add("X-TotalCount", count)
    if exclusions:
        resp.headers.add("X-Excluding", ",".join(exclusions))
    return resp

@app.route('/agencies')
@api_list
def agency_list(limit, offset):
    if g.request_format == "json":
        agencies = get_agencies(limit, offset)
        return render_json(agencies, limit, offset, get_agencies_count())
    else:
        agencies = get_agencies()
        return render_template('agencies/index.html', agencies=agencies)

@app.route('/agencies/<agency_id>')
def agency_detail(agency_id):
    agency = get_agency(agency_id)
    if g.request_format == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/agencies/<agency_id>/routes')
@api_list
def route_list(agency_id, limit, offset):
    agency = get_agency(agency_id)
    count = len(agency.route_ids)
    if g.request_format == "json":
        if limit:
            page = agency.route_ids[offset:offset+limit]
        else:
            page = agency.route_ids[offset:]
        routes = [get_route(agency_id, route_id) for route_id in page]
        return render_json(routes, limit, offset, count)
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
@api_list
def direction_list(agency_id, route_id, limit, offset):
    route = get_route(agency_id, route_id)
    count = len(route.direction_ids)
    if g.request_format == "json":
        if limit:
            page = route.direction_ids[offset:offset+limit]
        else:
            page = route.direction_ids[offset:]
        directions = [get_direction(agency_id, route_id, direction_id) for direction_id in page]
        return render_json(directions, limit, offset, count)
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
@api_list
def stop_list(agency_id, route_id, direction_id, limit, offset):
    direction = get_direction(agency_id, route_id, direction_id)
    count = len(direction.stop_ids)
    if g.request_format == "json":
        if limit:
            page = direction.stop_ids[offset:offset+limit]
        else:
            page = direction.stop_ids[g.offset:]
        stops = [get_stop(agency_id, route_id, direction_id, stop_id) for stop_id in page]
        return render_json(stops, limit, offset, count)
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
@api_list
def prediction_list(agency_id, route_id, direction_id, stop_id, limit, offset):
    predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
    if g.request_format == "twiml":
        twiml = get_twiml(predictions)
        return Response(twiml, mimetype="text/xml")
    else:
        count = len(predictions)
        if limit:
            predictions = predictions[offset:offset+limit]
        else:
            predictions = predictions[offset:]
        return render_json(predictions, limit, offset, count)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions/<trip_id>')
def prediction_detail(agency_id, route_id, direction_id, stop_id, trip_id):
    prediction = nextbus.get_prediction(agency_id, route_id, direction_id, stop_id, trip_id)
    if g.request_format == "twiml":
        twiml = get_twiml(prediction)
        return Response(twiml, mimetype="text/xml")
    else:
        return render_json(prediction)

