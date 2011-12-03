from buscall import app
from flask import g, Response
from google.appengine.api import urlfetch
import logging
import re
from decimal import Decimal
from urllib import urlencode
from buscall import cache
from buscall.util import clean_booleans, filter_keys
from recordtype import recordtype
import simplejson as json
from lxml import etree

Agency = recordtype("Agency", ['id', 'title', 'region', 
    ('short_title', None), ('route_ids', [])])
Route = recordtype("Route", ['id', 'agency_id', 'title', 'paths', ('direction_ids', []),
    ('latMin', None), ('latMax', None), ('lngMin', None), ('lngMax', None)])
Direction = recordtype("Direction", ['id', 'route_id', 'agency_id', 'title', ('name', ''), ('stop_ids', [])])
Stop = recordtype("Stop", ['id', 'direction_id', 'route_id', 'agency_id', 'title', 
    ('lat', None), ('lng', None)])
Point = recordtype("Point", ['lat', 'lng'])
PredictedBus = recordtype("PredictedBus", ['minutes', 'vehicle', 
    ('seconds', None), ('trip_id', None), ('block', None),  ('departure', None), 
    ('affected_by_layover', None), ('delayed', None), ('slowness', None)])

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?"
# cache durations
SHORT = 20
HOUR = 3600
DAY = 86400

class NextbusError(Exception):
    def __init__(self, message, retry):
        self.message = message
        self.retry = retry

    def __str__(self):
        return self.message

@app.errorhandler(NextbusError)
def handle_nextbus_error(error):
    if re.match(r'Could not get \w+ "[^"]+" for \w+ tag "[^"]+"', error.message) or \
       error.message.startswith("Invalid"):
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

def get_nextbus_xml(params):
    rpc = urlfetch.create_rpc()
    url = RPC_URL + urlencode(params)
    app.logger.info("fetching "+url)
    urlfetch.make_fetch_call(rpc, url)
    try:
        result = rpc.get_result()
        if result.status_code != 200:
            logging.error("status code %s for RPC with params %s" % (result.status_code, params))
    except urlfetch.DownloadError:
        logging.error("Download error: " + url)
        return None

    tree = etree.fromstring(result.content)
    error = tree.find('Error')
    if error is not None:
        raise NextbusError(error.text.strip(), error.attrib['shouldRetry'])
    # return tree # FIXME: cache cannot handle lxml parsed objects
    return etree.tostring(tree)

@cache.memoize(timeout=DAY)
def get_agencylist_xml():
    return get_nextbus_xml({
        "command": "agencyList",
    })

@cache.memoize(timeout=HOUR)
def get_routelist_xml(agency_id):
    return get_nextbus_xml({
        "a": agency_id,
        "command": "routeList",
    })

@cache.memoize(timeout=HOUR)
def get_route_xml(agency_id, route_id):
    return get_nextbus_xml({
        "a": agency_id,
        "r": route_id,
        "command": "routeConfig",
    })

@cache.memoize(timeout=SHORT)
def get_predictions_xml(agency_id, route_id, direction_id, stop_id):
    "Each physical stop has multiple IDs, depending on the bus direction."
    return get_nextbus_xml({
        "a": agency_id,
        "r": route_id,
        "d": direction_id,
        "s": stop_id,
        "command": "predictions",
    })

@cache.memoize(get_agencylist_xml.cache_timeout)
def get_agencies():
    agencies = []
    agencies_tree = etree.fromstring(get_agencylist_xml())
    if agencies_tree is None:
        # FIXME: handle the case where nextbus is unreachable
        return None
    for agency_el in agencies_tree.findall('agency'):
        id = agency_el.get("id") or agency_el.get("tag")
        agency = Agency(id = id, 
            title=agency_el.get("title"),
            short_title = agency_el.get("shortTitle"),
            region=agency_el.get("regionTitle"),
        )
        routelist_tree = etree.fromstring(get_routelist_xml(id))
        route_ids = []
        for route in routelist_tree.findall('route'):
            route_ids.append(route.get("id") or route.get("tag"))
        agency.route_ids = route_ids
        agencies.append(agency)
    return agencies

@cache.memoize(get_agencies.cache_timeout)
def get_agency(agency_id):
    agencies_tree = etree.fromstring(get_agencylist_xml())
    if agencies_tree is None:
        # FIXME: handle the case where nextbus is unreachable
        pass
    expr = '//agency[@id="{id}" or @tag="{id}"][1]'.format(id=agency_id)
    agency_els = agencies_tree.xpath(expr)
    try:
        agency_el = agency_els[0]
    except IndexError:
        raise NextbusError("Invalid agency", retry=False)
    agency = Agency(id = agency_id,
        title=agency_el.get("title"),
        short_title = agency_el.get("shortTitle"),
        region=agency_el.get("regionTitle"),
    )
    routelist_tree = etree.fromstring(get_routelist_xml(agency_id))
    route_ids = []
    for route in routelist_tree.findall('route'):
        route_ids.append(route.get("id") or route.get("tag"))
    agency.route_ids = route_ids
    return agency

@cache.memoize(get_route_xml.cache_timeout)
def get_route(agency_id, route_id):
    route_tree = etree.fromstring(get_route_xml(agency_id, route_id))
    route_el = route_tree.find('route')
    attrs = dict(route_el.attrib)
    attrs = clean_booleans(attrs)
    if "tag" in attrs and not "id" in attrs:
        attrs["id"] = attrs["tag"]
        del attrs["tag"]
    for lat in ("latMin", "latMax"):
        if lat in attrs:
            attrs[lat] = Decimal(attrs[lat])
    for lon in ("lonMin", "lonMax"):
        if lon in attrs:
            attrs[lon.replace("lon", "lng")] = Decimal(attrs[lon])
            del attrs[lon]
    paths = []
    for path_el in route_el.findall('path'):
        paths.append([Point(Decimal(p.get("lat")), Decimal(p.get("lon"))) for p in path_el])
    attrs["paths"] = paths
    direction_ids = [d.get("id") or d.get("tag") for d in route_el.findall('direction')]
    attrs["direction_ids"] = direction_ids
        
    attrs = filter_keys(attrs, Route._fields)
    attrs['agency_id'] = agency_id
    return Route(**attrs)

@cache.memoize(get_route_xml.cache_timeout)
def get_direction(agency_id, route_id, direction_id):
    route_tree = etree.fromstring(get_route_xml(agency_id, route_id))
    expr = '//route/direction[@id="{id}" or @tag="{id}"][1]'.format(id=direction_id)
    direction_els = route_tree.xpath(expr)
    try:
        direction_el = direction_els[0]
    except KeyError:
        raise NextbusError("Invalid direction", retry=False)

    attrs = dict(direction_el.attrib)
    stop_ids = [s.get("id") or s.get("tag") for s in direction_el]
    attrs["stop_ids"] = stop_ids

    attrs = filter_keys(attrs, Direction._fields)
    attrs["agency_id"] = agency_id
    attrs["route_id"] = route_id
    attrs["id"] = direction_id
    return Direction(**attrs)

@cache.memoize(get_route_xml.cache_timeout)
def get_stop(agency_id, route_id, direction_id, stop_id):
    route_tree = etree.fromstring(get_route_xml(agency_id, route_id))
    expr = '//route/stop[@id="{id}" or @tag="{id}"]'.format(id=stop_id)
    stop_els = route_tree.xpath(expr)
    try:
        stop_el = stop_els[0]
    except KeyError:
        raise NextbusError("Invalid stop", retry=False)
    attrs = dict(stop_el.attrib)
    attrs = filter_keys(attrs, Stop._fields)
    attrs["agency_id"] = agency_id
    attrs["route_id"] = route_id
    attrs["direction_id"] = direction_id
    attrs["id"] = stop_id
    return Stop(**attrs)

@cache.memoize(get_predictions_xml.cache_timeout)
def get_predictions(agency_id, route_id, direction_id, stop_id):
    predictions_tree = etree.fromstring(get_predictions_xml(agency_id, route_id, direction_id, stop_id))
    buses = []
    for prediction_el in predictions_tree.xpath('/body/predictions/direction/prediction'):
        buses.append(PredictedBus(
            minutes = int(prediction_el.get("minutes", 0)),
            seconds = int(prediction_el.get("seconds", 0)),
            vehicle = prediction_el.get("vehicle"),
            trip_id = prediction_el.get("tripTag"),
            block = prediction_el.get("block"),
            departure = prediction_el.get("isDeparture", "").lower() == "true",
            affected_by_layover = prediction_el.get("affectedByLayover", "").lower() == "true",
            delayed = prediction_el.get("delayed", "").lower() == "true",
            slowness = int(prediction_el.get("slowness", 0)),
        ))
    return buses

