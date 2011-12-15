from buscall import app
from flask import g, Response, url_for
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
from lxml.etree import ParseError

resource_uri = "resource_uri"

Point = recordtype("Point", ['lat', 'lng'])

AgencyRecord = recordtype("Agency", ['id', 'title', 'region',
    ('short_title', None), ('route_ids', [])])
class Agency(AgencyRecord):
    @property
    def url(self):
        return url_for('agency_detail', agency_id=self.id)

    def _as_url_dict(self):
        d = self._asdict()
        d[resource_uri] = self.url
        del d['route_ids']
        d['routes'] = [url_for('route_detail',
            agency_id=self.id, route_id=route_id)
            for route_id in self.route_ids]
        return d

RouteRecord = recordtype("Route", ['id', 'agency_id', 'title', 'paths', ('direction_ids', []),
    ('latMin', None), ('latMax', None), ('lngMin', None), ('lngMax', None)])
class Route(RouteRecord):
    @property
    def url(self):
        return url_for('route_detail', agency_id=self.agency_id, route_id=self.id)

    def _as_url_dict(self):
        d = self._asdict()
        d[resource_uri] = self.url
        del d['agency_id']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['direction_ids']
        d['directions'] = [url_for('direction_detail',
            agency_id=self.agency_id, route_id=self.id, direction_id=direction_id)
            for direction_id in self.direction_ids]
        return d

DirectionRecord = recordtype("Direction", ['id', 'route_id', 'agency_id', 'title', ('name', ''), ('stop_ids', [])])
class Direction(DirectionRecord):
    @property
    def url(self):
        return url_for('direction_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.id)

    def _as_url_dict(self):
        d = self._asdict()
        d[resource_uri] = self.url
        del d['agency_id']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_id']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        del d['stop_ids']
        d['stops'] = [url_for('stop_detail',
            agency_id=self.agency_id, route_id=self.route_id, direction_id=self.id, stop_id=stop_id)
            for stop_id in self.stop_ids]
        return d

StopRecord = recordtype("Stop", ['id', 'direction_id', 'route_id', 'agency_id', 'title',
    ('lat', None), ('lng', None)])
class Stop(StopRecord):
    @property
    def url(self):
        return url_for('stop_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.direction_id, stop_id=self.id)

    def _as_url_dict(self):
        d = self._asdict()
        d[resource_uri] = self.url
        del d['agency_id']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_id']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        del d['direction_id']
        d['direction'] = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id)
        d['predictions'] = url_for('prediction_list', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id, stop_id=self.id)
        return d

PredictedBusRecord = recordtype("PredictedBus", ['agency_id', 'route_id',
    'direction_id', 'stop_id', 'trip_id', 'minutes', 'vehicle',
    ('seconds', None), ('block', None),  ('departure', None),
    ('affected_by_layover', None), ('delayed', None), ('slowness', None)])
class PredictedBus(PredictedBusRecord):
    @property
    def url(self):
        return url_for('prediction_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.direction_id, stop_id=self.stop_id, trip_id=self.trip_id)
    @property
    def id(self):
        return self.trip_id

    def _as_url_dict(self):
        d = self._asdict()
        d[resource_uri] = self.url
        del d['agency_id']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_id']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        del d['direction_id']
        d['direction'] = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id)
        del d['stop_id']
        d['stop'] = url_for('stop_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id, stop_id=self.stop_id)
        return d

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
        raise NextbusError(error.text.strip(), error.attrib['shouldRetry'])
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
def get_agencies(limit=None, offset=0):
    agencies = []
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
    if limit:
        agency_els = agency_els[offset:offset+limit]
    else:
        agency_els = agency_els[offset:]
    for agency_el in agency_els:
        agency_id = agency_el.get("id") or agency_el.get("tag")
        agency = Agency(id = agency_id, 
            title = agency_el.get("title"),
            short_title = agency_el.get("shortTitle"),
            region = agency_el.get("regionTitle"),
        )
        xml = get_routelist_xml(agency_id)
        try:
            routelist_tree = etree.fromstring(xml)
        except ParseError, e:
            app.logger.error(xml)
            raise e
        route_ids = []
        for route in routelist_tree.findall('route'):
            route_ids.append(route.get("id") or route.get("tag"))
        agency.route_ids = route_ids
        agencies.append(agency)
    return agencies

def get_agencies_count():
    xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    return len(agencies_tree.findall('agency'))

@cache.memoize(get_agencies.cache_timeout)
def get_agency(agency_id):
    xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
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
        title = agency_el.get("title"),
        short_title = agency_el.get("shortTitle"),
        region = agency_el.get("regionTitle"),
    )
    xml = get_routelist_xml(agency_id)
    try:
        routelist_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    route_ids = []
    for route in routelist_tree.findall('route'):
        route_ids.append(route.get("id") or route.get("tag"))
    agency.route_ids = route_ids
    return agency

@cache.memoize(get_route_xml.cache_timeout)
def get_route(agency_id, route_id):
    xml = get_route_xml(agency_id, route_id)
    try:
        route_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
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
    xml = get_route_xml(agency_id, route_id)
    try:
        route_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    expr = '//route/direction[@id="{id}" or @tag="{id}"][1]'.format(id=direction_id)
    direction_els = route_tree.xpath(expr)
    try:
        direction_el = direction_els[0]
    except IndexError:
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
    xml = get_route_xml(agency_id, route_id)
    try:
        route_tree = etree.fromstring(xml)
    except ParseError, e:
        app.logger.error(xml)
        raise e
    expr = '//route/stop[@id="{id}" or @tag="{id}"]'.format(id=stop_id)
    stop_els = route_tree.xpath(expr)
    try:
        stop_el = stop_els[0]
    except IndexError:
        raise NextbusError("Invalid stop", retry=False)
    attrs = dict(stop_el.attrib)
    if "lat" in attrs:
        attrs["lat"] = Decimal(attrs["lat"])
    if "lon" in attrs:
        attrs["lng"] = Decimal(attrs["lon"])
    if "lng" in attrs:
        attrs["lng"] = Decimal(attrs["lng"])
    attrs = filter_keys(attrs, Stop._fields)
    attrs["agency_id"] = agency_id
    attrs["route_id"] = route_id
    attrs["direction_id"] = direction_id
    attrs["id"] = stop_id
    return Stop(**attrs)

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
        buses.append(PredictedBus(
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
    return PredictedBus(
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

