from buscall import app
from flask import request, g, Response
from google.appengine.api import urlfetch
from xml.etree import ElementTree as etree
import logging
import time
import re
from decimal import Decimal
from urllib import urlencode
from buscall import cache
from functools import wraps
from buscall.util import clean_booleans, filter_keys
from collections import OrderedDict
from recordtype import recordtype
import simplejson as json

Agency = recordtype("Agency", ['id', 'title'])
Route = recordtype("Route", ['id', 'title', 'directions', 'path', 
    ('latMin', None), ('latMax', None), ('lngMin', None), ('lngMax', None)])
FullRoute = recordtype("FullRoute", ['id', 'title', 'directions', 'path', 'stops',
    ('latMin', None), ('latMax', None), ('lngMin', None), ('lngMax', None)])
RouteID = recordtype("RouteID", ['id', 'title'])
Direction = recordtype("Direction", ['id', 'title', ('name', ''), ('stops', [])])
DirectionID = recordtype("DirectionID", ['id', 'title', ('name', '')])
Stop = recordtype("Stop", ['id', 'title', 
    ('lat', None), ('lng', None)])
Point = recordtype("Point", ['lat', 'lng'])
Prediction = recordtype("Prediction", ['buses', 'route', 'direction', 'stop', 
    ('time', None)])
PredictedBus = recordtype("PredictedBus", ['minutes', 'vehicle', 
    ('seconds', None), ('trip_id', None), ('block', None),  ('departure', None), 
    ('affectedByLayover', None), ('delayed', None), ('slowness', None)])

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?"
AGENCIES = {'mbta': Agency('mbta', "MBTA")}

class NextbusError(Exception):
    def __init__(self, message, shouldRetry):
        self.message = message
        self.retry = shouldRetry

    def __str__(self):
        return self.message

def errcheck_xml(func):
    @wraps(func)
    def wrapper(tree, *args, **kwargs):
        error = tree.find('Error')
        if error is not None:
            raise NextbusError(error.text.strip(), error.attrib['shouldRetry'])
        return func(tree, *args, **kwargs)
    return wrapper

@app.errorhandler(NextbusError)
def handle_nextbus_error(error):
    if re.match(r'Could not get \w+ "[^"]+" for \w+ tag "[^"]+"', error.message):
        status = 404
    else:
        status = 400
    if g.request_format == "json":
        message = json.dumps({
            "message": error.message,
            "should_retry": bool(error.retry),
        })
        mimetype = "application/json"
    else:
        message = error.message
        if error.retry:
            message += " You may retry this request."
        else:
            message += " You may not retry this request."
        mimetype = None
    return Response(message, status=status, mimetype=mimetype)

@cache.memoize(timeout=3600)
def get_routes(agency_id, use_dicts=True):
    rpc = urlfetch.create_rpc()
    url = RPC_URL + urlencode({
        "a": agency_id,
        "command": "routeList",
    })
    urlfetch.make_fetch_call(rpc, url)
    try:
        result = rpc.get_result()
        if result.status_code != 200:
            logging.error("index_routes RPC returned status code %s" % result.status_code)
    except urlfetch.DownloadError:
        logging.error("Download error: " + url)
        return None

    tree = etree.fromstring(result.content)
    return parse_index_xml(tree, use_dicts)

@errcheck_xml
def parse_index_xml(tree, use_dicts=True):
    if use_dicts:
        parsed = OrderedDict()
        def add(d, obj):
            d[obj.id] = obj
    else:
        parsed = []
        def add(l, obj):
            l.append(obj)
    for route in tree.findall('route'):
        route_info = clean_booleans(route.attrib)
        if "tag" in route_info and "id" not in route_info:
            route_info['id'] = route_info['tag']
            del route_info['tag']
        route_info = filter_keys(route_info, RouteID._fields)
        route = RouteID(**route_info)
        add(parsed, route)
    return parsed

@cache.memoize(timeout=3600)
def get_route(agency_id, route_id, full=True, use_dicts=False):
    rpc = urlfetch.create_rpc()
    url = RPC_URL + urlencode({
        "a": agency_id,
        "r": route_id,
        "command": "routeConfig",
    })
    urlfetch.make_fetch_call(rpc, url)
    try:
        result = rpc.get_result()
        if result.status_code != 200:
            logging.error("show_route %s RPC returned status code %s" % (route_id, result.status_code))
    except urlfetch.DownloadError:
        logging.error("Download error: " + url)
        return None
    
    tree = etree.fromstring(result.content)
    route = parse_route_xml(tree, full, use_dicts)

    return route

@errcheck_xml
def parse_route_xml(tree, full=True, use_dicts=False):
    if use_dicts:
        def add(d, obj):
            d[obj.id] = obj
    else:
        def add(l, obj):
            l.append(obj)

    routeElem = tree.find('route')
    # basic route attributes
    routeDict = clean_booleans(routeElem.attrib)
    if "tag" in routeDict and "id" not in routeDict:
        routeDict['id'] = routeDict['tag']
        del routeDict['tag']
    for tag in ('latMin', 'latMax', 'lonMin', 'lonMax'):
        if tag in routeDict:
            newtag = tag.replace('lon', 'lng')
            value = Decimal(routeDict[tag])
            del routeDict[tag]
            routeDict[newtag] = value

    if full:
        # detailed info about stops
        if use_dicts:
            stops = OrderedDict()
        else:
            stops = []
        for stop in routeElem.findall("stop"):
            stop_info = stop.attrib
            if 'tag' in stop_info and 'id' not in stop_info:
                stop_info['id'] = stop_info['tag']
                del stop_info['tag']
            for tag in ('lat', 'lon'):
                if tag in stop_info:
                    newtag = tag.replace('lon', 'lng')
                    value = Decimal(stop_info[tag])
                    del stop_info[tag]
                    stop_info[newtag] = value
            if "stopId" in stop_info:
                del stop_info["stopId"]
            stop_info = clean_booleans(stop_info)
            stop_info = filter_keys(stop_info, Stop._fields)
            stop = Stop(**stop_info)
            add(stops, stop)
        routeDict['stops'] = stops

    # directions (inbound, outbound)
    if use_dicts:
        directions = OrderedDict()
    else:
        directions = []
    for direction in routeElem.findall('direction'):
        dir_info = direction.attrib
        if 'tag' in dir_info and 'id' not in dir_info:
            dir_info['id'] = dir_info['tag']
            del dir_info['tag']
        dir_info = clean_booleans(dir_info)
        if full:
            # add stop ids
            dir_info['stops'] = [stop.get('tag') for stop in direction.findall('stop')]
            dir_info = filter_keys(dir_info, Direction._fields)
            direction = Direction(**dir_info)
        else:
            dir_info = filter_keys(dir_info, DirectionID._fields)
            direction = DirectionID(**dir_info)
        add(directions, direction)
    routeDict['directions'] = directions
    
    # path of lat/long points
    route_path = []
    for path in routeElem.findall('path'):
        segment = []
        for point in path.findall('point'):
            lat = point.get('lat')
            lng = point.get('lon') or point.get('lng')
            segment.append(Point(Decimal(lat), Decimal(lng)))
        route_path.append(segment)
    routeDict['path'] = route_path

    if full:
        routeDict = filter_keys(routeDict, FullRoute._fields)
        route = FullRoute(**routeDict)
    else:
        routeDict = filter_keys(routeDict, Route._fields)
        route = Route(**routeDict)
    return route

def get_direction(agency_id, route_id, direction_id):
    route = get_route(agency_id, route_id, use_dicts=True)
    return route.directions[direction_id]

def get_stop(agency_id, route_id, direction_id, stop_id):
    route = get_route(agency_id, route_id, use_dicts=True)
    return route.stops[stop_id]

@cache.memoize(timeout=20)
def get_predictions(agency_id, route_id, direction_id, stop_id):
    "Each physical stop has multiple IDs, depending on the bus direction."
    rpc = urlfetch.create_rpc()
    url = RPC_URL + urlencode({
        "a": agency_id,
        "r": route_id,
        "d": direction_id,
        "s": stop_id,
        "command": "predictions",
    })
    urlfetch.make_fetch_call(rpc, url)
    try:
        result = rpc.get_result()
        if result.status_code != 200:
            logging.error("predict_for_stop %s, %s RPC returned status code %s" % (route_id, stop_id, result.status_code))
    except urlfetch.DownloadError:
        logging.error("Download error: " + url)
        return None
    
    tree = etree.fromstring(result.content)
    return parse_predict_xml(tree, direction_id)

@errcheck_xml
def parse_predict_xml(tree, direction_id=""):
    predictions_el = tree.find('predictions')
    stop = Stop(id=predictions_el.get('stopTag'), title=predictions_el.get('stopTitle'))
    routeID = RouteID(id=predictions_el.get('routeTag'), title=predictions_el.get('routeTitle'))

    direction_el = predictions_el.find('direction')
    if direction_el is not None:
        # we have predictions
        first_prediction_el = direction_el.find('prediction')
        directionID = DirectionID(first_prediction_el.get('dirTag'), direction_el.get('title'))
        epoch_time = time.localtime(int(first_prediction_el.get('epochTime')))

        buses = []
        for prediction_el in direction_el.findall('prediction'):
            bus = prediction_el.attrib
            if 'departure' not in bus and 'isDeparture' in bus:
                bus['departure'] = bus['isDeparture']
                del bus['isDeparture']
            if 'trip_id' not in bus and 'tripTag' in bus:
                bus['trip_id'] = bus['tripTag']
                del bus['tripTag']
            bus = clean_booleans(bus)
            bus['minutes'] = int(bus['minutes'])
            bus['seconds'] = int(bus['seconds'])

            bus = filter_keys(bus, PredictedBus._fields)
            buses.append(PredictedBus(**bus))

        return Prediction(buses=buses, time=epoch_time, route=routeID, direction=directionID, stop=stop)
    
    else: # no buses predicted
        directionID = DirectionID(direction_id, predictions_el.get('dirTitleBecauseNoPredictions'))
        return Prediction(buses=[], epoch_time=None, route=routeID, direction=directionID, stop=stop)

