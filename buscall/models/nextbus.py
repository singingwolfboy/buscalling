from google.appengine.api import urlfetch
from xml.etree import ElementTree as etree
import logging
import time
from decimal import Decimal
from buscall import cache
from functools import wraps
from buscall.util import url_params, clean_booleans
try:
    from collections import OrderedDict
except ImportError:
    from collections_backport import OrderedDict
try:
    from collections import namedtuple
except ImportError:
    from collections_backport import namedtuple

Agency = namedtuple("Agency", ['id', 'title'])
Route = namedtuple("Route", ['id', 'title', 'directions', 'stops', 'path', 'latMin', 'latMax', 'lonMin', 'lonMax'])
RouteID = namedtuple("RouteID", ['id', 'title'])
Direction = namedtuple("Direction", ['id', 'title', 'name', 'stop_ids'])
DirectionID = namedtuple("DirectionID", ['id', 'title'])
Stop = namedtuple("Stop", ['id', 'title', 'lat', 'lon'])
StopID = namedtuple("StopID", ['id', 'title'])
Point = namedtuple("Point", ['lat', 'lon'])
Prediction = namedtuple("Prediction", ["buses", "time", "route", "direction", "stop"])
PredictedBus = namedtuple("PredictedBus", ["minutes", "seconds", "vehicle", "trip_id", "block", "departure", "affectedByLayover"])


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


@cache.memoize(timeout=3600)
def get_routes(agency_id):
    rpc = urlfetch.create_rpc()
    url = RPC_URL + url_params({
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

    tree = etree.fromstring(result.content)
    return parse_index_xml(tree)

@errcheck_xml
def parse_index_xml(tree):
    parsed = OrderedDict()
    for route in tree.findall('route'):
        route_info = clean_booleans(route.attrib)
        if "tag" in route_info and "id" not in route_info:
            route_info['id'] = route_info['tag']
            del route_info['tag']
        route = RouteID(**route_info)
        parsed[route.id] = route
    return parsed

@cache.memoize(timeout=3600)
def get_route(agency_id, route_id, use_dicts=False):
    rpc = urlfetch.create_rpc()
    url = RPC_URL + url_params({
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
    
    tree = etree.fromstring(result.content)
    route = parse_route_xml(tree, use_dicts)

    return route

@errcheck_xml
def parse_route_xml(tree, use_dicts=False):
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
            routeDict[tag] = Decimal(routeDict[tag])

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
                stop_info[tag] = Decimal(stop_info[tag])
        if "stopId" in stop_info:
            del stop_info["stopId"]
        stop_info = clean_booleans(stop_info)
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
        # make list of stops
        dir_info['stop_ids'] = [stop.get('tag') for stop in direction.findall('stop')]
        dir_info = clean_booleans(dir_info)
        for key in dir_info.keys():
            if key not in Direction._fields:
                del dir_info[key]
        add(directions, Direction(**dir_info))
    routeDict['directions'] = directions
    
    # path of lat/long points
    route_path = []
    for path in routeElem.findall('path'):
        segment = [Point(Decimal(point.get('lat')), Decimal(point.get('lon'))) 
            for point in path.findall('point')]
        route_path.append(segment)
    routeDict['path'] = route_path

    for key in routeDict.keys():
        if key not in Route._fields:
            del routeDict[key]

    return Route(**routeDict)

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
    url = RPC_URL + url_params({
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
    
    tree = etree.fromstring(result.content)
    return parse_predict_xml(tree, direction_id)

@errcheck_xml
def parse_predict_xml(tree, direction_id=""):
    predictions_el = tree.find('predictions')
    stopID = StopID(predictions_el.get('stopTag'), predictions_el.get('stopTitle'))
    routeID = RouteID(predictions_el.get('routeTag'), predictions_el.get('routeTitle'))

    direction_el = predictions_el.find('direction')
    if direction_el:
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
            for key in bus.keys():
                if not key in PredictedBus._fields:
                    del bus[key]
            bus = clean_booleans(bus)
            bus['minutes'] = int(bus['minutes'])
            bus['seconds'] = int(bus['seconds'])
            if 'affectedByLayover' not in bus:
                bus['affectedByLayover'] = None
            buses.append(PredictedBus(**bus))

        return Prediction(buses=buses, time=epoch_time, route=routeID, direction=directionID, stop=stopID)
    
    else: # no buses predicted
        directionID = DirectionID(direction_id, predictions_el.get('dirTitleBecauseNoPredictions'))
        return Prediction(buses=[], epoch_time=None, route=routeID, direction=directionID, stop=stopID)

