from buscall import app
from ndb import Key
from flask import g, Response
from google.appengine.api import urlfetch
import logging
import re
from decimal import Decimal
from urllib import urlencode
from buscall import cache
import simplejson as json
from lxml import etree
from lxml.etree import ParseError
from google.appengine.api.datastore_types import GeoPt
from google.appengine.ext import deferred
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction

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

    try:
        tree = etree.fromstring(result.content)
    except ParseError, e:
        app.logger.error(result.content)
        raise e
    error = tree.find('Error')
    if error is not None:
        retry = error.attrib.get('shouldRetry')
        if retry is None:
            retry = False
        if not isinstance(retry, bool):
            retry = retry.lower() == "true"
        raise NextbusError(error.text.strip(), retry)
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

# This runs in a deferred() handler
def update_agency_and_children(agency_id):
    al_xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(al_xml)
    except ParseError, e:
        app.logger.error(al_xml)
        raise e
    expr = '//agency[@id="{id}" or @tag="{id}"][1]'.format(id=agency_id)
    agency_els = agencies_tree.xpath(expr)
    try:
        agency_el = agency_els[0]
    except IndexError:
        raise NextbusError("Invalid agency", retry=False)
    agency_key = Key(Agency, agency_id)
    agency_min_lat = 90
    agency_min_lng = 180
    agency_max_lat = -90
    agency_max_lng = -180
    route_keys = []
    rl_xml = get_routelist_xml(agency_id)
    try:
        routelist_tree = etree.fromstring(rl_xml)
    except ParseError, e:
        app.logger.error(rl_xml)
        raise e
    for route_el in routelist_tree.findall('route'):
        route_id = route_el.get("id") or route_el.get("tag")
        route_key = Key(Route, route_id)
        rc_xml = get_route_xml(agency_id, route_id)
        try:
            route_tree = etree.fromstring(rc_xml)
        except ParseError, e:
            app.logger.error(rc_xml)
            raise e

        for stop_el in route_tree.xpath('//route/stop'):
            stop_id = stop_el.get("id") or stop_el.get("tag")
            expr = '//route/direction/stop[@id="{id}" or @tag="{id}"]/..'.format(id=stop_id)
            direction_el = route_tree.xpath(expr)[0]
            direction_id = direction_el.get("id") or direction_el.get("tag")
            direction_key = Key(Direction, direction_id)
            lat = stop_el.get("lat")
            lng = stop_el.get("lng") or stop_el.get("lon")
            stop = Stop.get_or_update(id=stop_id,
                name = stop_el.get("name") or stop_el.get("title"),
                point = GeoPt(lat, lng),
                agency_key = agency_key,
                route_key = route_key,
                direction_key = direction_key)

        direction_keys = []
        for direction_el in route_tree.xpath('//route/direction'):
            direction_id = direction_el.get("id") or direction_el.get("tag")
            stop_keys = []
            for stop_el in direction_el.find("stop"):
                stop_id = stop_el.get("id") or stop_el.get("tag")
                stop_keys.append(Key(Stop, stop_id))
            direction = Direction.get_or_update(id=direction_id,
                name = direction_el.get("name"),
                title = direction_el.get("title"),
                agency_key = agency_key,
                route_key = route_key,
                stop_keys = stop_keys)
            direction_keys.append(direction.key)

        min_lat = route_el.get("minLat")
        if min_lat:
            min_lat = Decimal(min_lat)
            if min_lat < agency_min_lat:
                agency_min_lat = min_lat
        min_lng = route_el.get("minLng") or route_el.get("minLon")
        if min_lng:
            min_lng = Decimal(min_lng)
            if min_lng < agency_min_lng:
                agency_min_lng = min_lng
        max_lat = route_el.get("maxLat")
        if max_lat:
            max_lat = Decimal(max_lat)
            if max_lat > agency_max_lat:
                agency_max_lat = max_lat
        max_lng = route_el.get("maxLng") or route_el.get("maxLon")
        if max_lng:
            max_lng = Decimal(max_lng)
            if max_lng > agency_max_lng:
                agency_max_lng = max_lng

        if min_lat and min_lng:
            min_point = GeoPt(min_lat, min_lng)
        else:
            min_point = None
        if max_lat and max_lng:
            max_point = GeoPt(max_lat, max_lng)
        else:
            max_point = None

        paths = []
        for path_el in route_el.findall('path'):
            subpaths = []
            for point_el in path_el.findall('point'):
                lat = point_el.get("lat")
                lng = point_el.get("lng") or point_el.get("lon")
                subpaths.append(GeoPt(lat, lng))
            paths.append(subpaths)

        route = Route.get_or_insert(id=route_id,
            name = route_el.get("name") or route_el.get("title"),
            min_pt = min_point,
            max_pt = max_point,
            paths = paths,
            direction_keys = direction_keys)
        route_keys.append(route.key)

    agency = Agency.get_or_insert(id=agency_id,
        name = agency_el.get("name") or agency_el.get("title"),
        short_name = agency_el.get("shortName") or agency_el.get("shortTitle"),
        region = agency_el.get("region"),
        min_pt = GeoPt(agency_min_lat, agency_min_lng),
        max_pt = GeoPt(agency_max_lat, agency_max_lng),
        route_keys = route_keys)

def fire_agency_deferreds():
    xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    if agencies_tree is None:
        # FIXME: handle the case where nextbus is unreachable
        return None
    agency_els = agencies_tree.findall('agency')
    for agency_el in agency_els:
        agency_id = agency_el.get("id") or agency_el.get("tag")
        if agency_id:
            deferred.defer(update_agency_and_children, agency_id)

@cache.memoize(get_predictions_xml.cache_timeout)
def get_predictions(agency_id, route_id, direction_id, stop_id):
    xml = get_predictions_xml(agency_id, route_id, direction_id, stop_id)
    try:
        predictions_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    buses = []
    for prediction_el in predictions_tree.xpath('/body/predictions/direction/prediction'):
        buses.append(BusPrediction(
            agency_id = agency_id,
            route_id = route_id,
            direction_id = direction_id,
            stop_id = stop_id,
            trip_id = prediction_el.get("tripTag"),
            minutes = int(prediction_el.get("minutes", 0)),
            seconds = int(prediction_el.get("seconds", 0)),
            vehicle = prediction_el.get("vehicle"),
            block = prediction_el.get("block"),
            departure = prediction_el.get("isDeparture", "").lower() == "true",
            affected_by_layover = prediction_el.get("affectedByLayover", "").lower() == "true",
            delayed = prediction_el.get("delayed", "").lower() == "true",
            slowness = int(prediction_el.get("slowness", 0)),
        ))
    return buses

@cache.memoize(get_predictions_xml.cache_timeout)
def get_prediction(agency_id, route_id, direction_id, stop_id, trip_id):
    xml = get_predictions_xml(agency_id, route_id, direction_id, stop_id)
    try:
        predictions_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    expr = '//predictions/direction/prediction[@tripId="{id}" or @tripTag="{id}"]'.format(id=trip_id)
    prediction_els = predictions_tree.xpath(expr)
    try:
        prediction_el = prediction_els[0]
    except IndexError:
        raise NextbusError("Invalid prediction", retry=False)
    return BusPrediction(
        agency_id = agency_id,
        route_id = route_id,
        direction_id = direction_id,
        stop_id = stop_id,
        trip_id = trip_id,
        minutes = int(prediction_el.get("minutes", 0)),
        seconds = int(prediction_el.get("seconds", 0)),
        vehicle = prediction_el.get("vehicle"),
        block = prediction_el.get("block"),
        departure = prediction_el.get("isDeparture", "").lower() == "true",
        affected_by_layover = prediction_el.get("affectedByLayover", "").lower() == "true",
        delayed = prediction_el.get("delayed", "").lower() == "true",
        slowness = int(prediction_el.get("slowness", 0)),
    )

