from buscall import app
from flask import render_template, request, Response, g, abort
from .util import render_json
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction
from buscall.models.twilio import get_twiml
from functools import wraps
from ndb import Key

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
        if kwargs['limit'] < 1:
            kwargs['limit'] = None

        if not 'offset' in kwargs:
            offset = request.args.get('offset') or request.headers.get('X-Offset')
            try:
                kwargs['offset'] = int(offset)
            except (ValueError, TypeError):
                kwargs['offset'] = 0
        if kwargs['offset'] < 1:
            kwargs['offset'] = None

        return func(*args, **kwargs)
    return wrapper

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
    agency = agency_key.get() or abort(404)
    routes_qry = Route.query(Route.agency_key == agency_key)
    if g.request_format == "json":
        routes = routes_qry.iter(limit=limit, offset=offset)
        return render_json(routes, limit, offset, routes_qry.count())
    else:
        ctx = dict(
            agency = agency,
            routes = routes_qry,
            # count = routes_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>')
def route_detail(agency_id, route_id):
    fctx = locals()  # format context
    route_key = Key(Route, "{agency_id}|{route_id}".format(**fctx))
    route = route_key.get() or abort(404)
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
    fctx = locals()  # format context
    agency_key = Key(Agency, agency_id)
    agency = agency_key.get() or abort(404)
    route_key = Key(Route, "{agency_id}|{route_id}".format(**fctx))
    route = route_key.get() or abort(404)
    directions_qry = Direction.query(Direction.route_key == route_key)
    if g.request_format == "json":
        directions = directions_qry.iter(limit=limit, offset=offset)
        return render_json(directions, limit, offset, directions_qry.count())
    else:
        ctx = dict(
            agency = agency,
            route = route,
            directions = directions_qry,
            # count = directions_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>')
def direction_detail(agency_id, route_id, direction_id):
    fctx = locals()  # format context
    agency_key = Key(Agency, agency_id)
    route_key = Key(Route, "{agency_id}|{route_id}".format(**fctx))
    direction_key = Key(Direction, "{agency_id}|{route_id}|{direction_id}".format(**fctx))
    direction = direction_key.get() or abort(404)
    if g.request_format == "json":
        return render_json(direction)
    else:
        ctx = dict(
            agency = agency_key.get() or abort(404),
            route = route_key.get() or abort(404),
            direction = direction,
        )
        return render_template('directions/show.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops')
@api_list
def stop_list(agency_id, route_id, direction_id, limit, offset):
    fctx = locals()  # format context
    agency_key = Key(Agency, agency_id)
    agency = agency_key.get() or abort(404)
    route_key = Key(Route, "{agency_id}|{route_id}".format(**fctx))
    route = route_key.get() or abort(404)
    direction_key = Key(Direction, "{agency_id}|{route_id}|{direction_id}".format(**fctx))
    direction = direction_key.get() or abort(404)
    stops_qry = Stop.query(Stop.direction_key == direction_key)
    if g.request_format == "json":
        stops = stops_qry.iter(limit=limit, offset=offset)
        return render_json(stops, limit, offset, stops_qry.count())
    else:
        ctx = dict(
            agency = agency,
            route = route,
            direction = direction,
            stops = stops_qry,
            # count = stops_qry.count(),
        )
        return render_template('routes/index.html', **ctx)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>')
def stop_detail(agency_id, route_id, direction_id, stop_id):
    fctx = locals()  # format context
    stop_key = Key(Stop, "{agency_id}|{route_id}|{direction_id}|{stop_id}".format(**fctx))
    stop = stop_key.get() or abort(404)
    if g.request_format == "json":
        return render_json(stop)
    else:
        agency_key = Key(Agency, agency_id)
        route_key = Key(Route, "{agency_id}|{route_id}".format(**fctx))
        direction_key = Key(Direction, "{agency_id}|{route_id}|{direction_id}".format(**fctx))
        ctx = dict(
            agency = agency_key.get() or abort(404),
            route = route_key.get() or abort(404),
            direction = direction_key.get() or abort(404),
            stop = stop,
            bus_predictions = BusPrediction.query(BusPrediction.stop_key == stop.key)
        )
        return render_template('stops/show.html', **ctx)

@app.route('/predictions/<agency_id>/<route_id>/<direction_id>/<stop_id>')
@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions')
@api_list
def prediction_list(agency_id, route_id, direction_id, stop_id, limit, offset):
    # Note that because the query() method was overridden on the BusPrediction class,
    # bus_predictions is NOT a Query object, but a list of BusPrediction objects.
    bus_predictions = BusPrediction.query(
        agency_id = agency_id,
        route_id = route_id,
        direction_id = direction_id,
        stop_id = stop_id)
    if g.request_format == "twiml":
        twiml = get_twiml(bus_predictions)
        return Response(twiml, mimetype="text/xml")
    else:
        count = len(bus_predictions)
        if offset:
            if limit:
                end = offset + limit
                bus_predictions = bus_predictions[offset:end]
            else:
                bus_predictions = bus_predictions[offset:]
        return render_json(bus_predictions, limit, offset, count)

@app.route('/agencies/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/predictions/<trip_id>')
def prediction_detail(agency_id, route_id, direction_id, stop_id, trip_id):
    bus_predictions = BusPrediction.query(
        agency_id = agency_id,
        route_id = route_id,
        direction_id = direction_id,
        stop_id = stop_id,
        trip_id = trip_id)
    try:
        bus_prediction = bus_predictions[0]
    except IndexError:
        abort(404)
    if g.request_format == "twiml":
        twiml = get_twiml(bus_prediction)
        return Response(twiml, mimetype="text/xml")
    else:
        return render_json(bus_prediction)

