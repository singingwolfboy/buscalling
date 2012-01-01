from buscall import app
from flask import render_template, request, Response, g, abort
# from buscall.models import nextbus_api
from buscall.models.twilio import get_twiml
import simplejson as json
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction
from functools import wraps
from ndb import Key

__all__ = ['agency_list', 'agency_detail', 'route_list', 'route_detail',
        'direction_list', 'direction_detail', 'stop_list', 'stop_detail',
        # 'prediction_list', 'prediction_detail',
        'render_json']

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
    # TODO: pull limit and offset from QueryIterator, rather than being passed in;
    # calculate count automatically rather than being passed in.

    # get exclusion list
    exclude = request.args.get('exclude') or request.headers.get('X-Exclude')
    if exclude:
        exclusions = [e.strip() for e in exclude.split(",")]
    else:
        exclusions = []
    # get dictionar(ies)
    def process(model):
        if hasattr(model, "_as_url_dict"):
            ret = model._as_url_dict()
        else:
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
        agencies = Agency.query().order(Agency.key).iter(limit=limit, offset=offset)
        return render_json(agencies, limit, offset, Agency.query().count())
    else:
        agencies = Agency.query()
        return render_template('agencies/index.html', agencies=agencies)

@app.route('/agencies/<agency_id>')
def agency_detail(agency_id):
    agency = Key(Agency, agency_id).get() or abort(404)
    if g.request_format == "json":
        return render_json(agency)
    else:
        return render_template('agencies/show.html', agency=agency)

@app.route('/agencies/<agency_id>/routes')
@api_list
def route_list(agency_id, limit, offset):
    agency_key = Key(Agency, agency_id)
    routes_qry = Route.query(Route.agency_key == agency_key)
    if g.request_format == "json":
        routes = routes_qry.iter(limit=limit, offset=offset)
        return render_json(routes, limit, offset, routes_qry.count())
    else:
        ctx = dict(
            agency = agency_key.get() or abort(404),
            routes = routes_qry,
            # count = routes_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>')
def route_detail(agency_id, route_id):
    route = Key(Route, route_id).get() or abort(404)
    if g.request_format == "json":
        return render_json(route)
    else:
        ctx = dict(
            agency = Key(Agency, agency_id).get() or abort(404),
            route = route,
        )
        return render_template('routes/show.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions')
@api_list
def direction_list(agency_id, route_id, limit, offset):
    agency_key = Key(Agency, agency_id)
    route_key = Key(Route, route_id)
    directions_qry = Direction.query(Direction.agency_key == agency_key,
        Direction.route_key == route_key)
    if g.request_format == "json":
        directions = directions_qry.iter(limit=limit, offset=offset)
        return render_json(directions, limit, offset, directions_qry.count())
    else:
        ctx = dict(
            agency = agency_key.get() or abort(404),
            route = route_key.get() or abort(404),
            directions = directions_qry,
            # count = directions_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>')
def direction_detail(agency_id, route_id, direction_id):
    direction = Key(Direction, direction_id).get() or abort(404)
    if g.request_format == "json":
        return render_json(direction)
    else:
        ctx = dict(
            agency = Key(Agency, agency_id).get() or abort(404),
            route = Key(Route, route_id).get() or abort(404),
            direction = direction,
        )
        return render_template('directions/show.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops')
@api_list
def stop_list(agency_id, route_id, direction_id, limit, offset):
    agency_key = Key(Agency, agency_id)
    route_key = Key(Route, route_id)
    direction_key = Key(Direction, direction_id)
    stops_qry = Stop.query(Stop.agency_key == agency_key, Stop.route_key == route_key,
        Stop.direction_key == direction_key)
    if g.request_format == "json":
        stops = stops_qry.iter(limit=limit, offset=offset)
        return render_json(stops, limit, offset, stops_qry.count())
    else:
        ctx = dict(
            agency = agency_key.get() or abort(404),
            route = route_key.get() or abort(404),
            direction = direction_key.get() or abort(404),
            stops = stops_qry,
            # count = stops_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>')
def stop_detail(agency_id, route_id, direction_id, stop_id):
    stop = Key(Stop, stop_id).get() or abort(404)
    if g.request_format == "json":
        return render_json(stop)
    else:
        agency_key = Key(Agency, agency_id)
        route_key = Key(Route, route_id)
        direction_key = Key(Direction, direction_id)
        ctx = dict(
            agency = agency_key.get() or abort(404),
            route = route_key.get() or abort(404),
            direction = direction_key.get() or abort(404),
            stop = stop,
            bus_predictions = BusPrediction.query(
                BusPrediction.agency_key == agency_key,
                BusPrediction.route_key == route_key,
                BusPrediction.direction_key == direction_key,
                BusPrediction.stop_key == stop.key)
        )
        return render_template('stops/show.html', **ctx)

"""
@app.route('/predictions/<agency_id>/<route_id>/<direction_id>/<stop_id>')
@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions')
@api_list
def prediction_list(agency_id, route_id, direction_id, stop_id, limit, offset):
    predictions = nextbus_api.get_predictions(agency_id, route_id, direction_id, stop_id)
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
    prediction = nextbus_api.get_prediction(agency_id, route_id, direction_id, stop_id, trip_id)
    if g.request_format == "twiml":
        twiml = get_twiml(prediction)
        return Response(twiml, mimetype="text/xml")
    else:
        return render_json(prediction)

"""
