import time
import datetime
from google.appengine.ext.db import GqlQuery
from buscall import app
from buscall.util import DAYS_OF_WEEK
from flask import redirect, url_for
from google.appengine.api.datastore_types import GeoPt
from google.appengine.ext import deferred
from buscall.models.nextbus import Agency, Route, Direction, Stop
from ndb import Key
from decimal import Decimal
from lxml import etree
import simplejson as json
from buscall.models.nextbus_api import NextbusError
from buscall.models.nextbus_api import get_agencylist_xml, get_routelist_xml, get_route_xml

@app.route('/tasks/poll')
def poll(struct_time=None):
    """
    This function is the workhorse of the whole application. When called,
    it checks the current time, pulls listeners from the datastore that are
    currently active, and then polls the bus routes for those listeners.
    This function is designed to be run once a minute (or more!) through cron.
    """
    if struct_time is None:
        struct_time = time.localtime() # current time

    # get all currently active listeners
    listeners = GqlQuery("SELECT * FROM BusListener WHERE " +
        DAYS_OF_WEEK[struct_time.tm_wday] + " = True AND start <= :time AND seen = False",
        time="TIME(%d, %d, %d)" % (struct_time.tm_hour, struct_time.tm_min, struct_time.tm_sec))
    for listener in listeners:
        if not listener.start <= datetime.time(struct_time.tm_hour, struct_time.tm_min, struct_time.tm_sec):
            continue # should have been filtered out by GqlQuery, but wasn't
        predictions = listener.get_predictions()
        for notification in listener.notifications:
            for bus in predictions:
                if notification.minutes == bus.minutes:
                    notification.execute(bus.minutes)

    return redirect(url_for("lander"), 303)

@app.route('/tasks/reset_seen_flags')
def reset_seen_flags():
    seen = GqlQuery("SELECT * FROM BusListener WHERE seen = True")
    for listener in seen:
        if listener.recur:
            # reset the "seen" flag
            listener.seen = False
            listener.put()
        else:
            # the listener has run, and it shouldn't run again, so delete it
            listener.delete()
    executed = GqlQuery("SELECT * FROM BusNotification WHERE executed = True")
    for notification in executed:
        notification.executed = False
        notification.put()
    return redirect(url_for("lander"), 303)

# This runs in a deferred() handler
@app.route('/tasks/nextbus/update/<agency_id>')
def update_agency_and_children(agency_id):
    stop_count = 0
    direction_count = 0
    route_count = 0
    al_xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(al_xml)
    except etree.ParseError, e:
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
    except etree.ParseError, e:
        app.logger.error(rl_xml)
        raise e
    for route_stub_el in routelist_tree.findall('route'):
        route_id = route_stub_el.get("id") or route_stub_el.get("tag")
        route_key = Key(Route, "{0}|{1}".format(agency_id, route_id))
        rc_xml = get_route_xml(agency_id, route_id)
        try:
            route_tree = etree.fromstring(rc_xml)
        except etree.ParseError, e:
            app.logger.error(rc_xml)
            raise e
        route_el = route_tree.find('route')

        direction_association_warning_count = 0
        for stop_el in route_tree.xpath('//route/stop'):
            stop_id = stop_el.get("id") or stop_el.get("tag")
            expr = '//route/direction/stop[@id="{id}" or @tag="{id}"]/..'.format(id=stop_id)
            direction_els = route_tree.xpath(expr)
            try:
                direction_el = direction_els[0]
            except IndexError:
                app.logger.warning("Couldn't find a <direction> association for <stop> " + stop_id)
                direction_association_warning_count += 1
                continue
            direction_id = direction_el.get("id") or direction_el.get("tag")
            direction_key = Key(Direction, "{0}|{1}|{2}".format(agency_id, route_id, direction_id))
            stop_key = Key(Stop, "{0}|{1}|{2}|{3}".format(agency_id, route_id, direction_id, stop_id))
            lat = stop_el.get("lat")
            lng = stop_el.get("lng") or stop_el.get("lon")
            stop = Stop(
                key = stop_key,
                name = stop_el.get("name") or stop_el.get("title"),
                point = GeoPt(lat, lng),
                agency_key = agency_key,
                route_key = route_key,
                direction_key = direction_key)
            stop.put()
            stop_count += 1

        direction_keys = []
        for direction_el in route_tree.xpath('//route/direction'):
            direction_id = direction_el.get("id") or direction_el.get("tag")
            direction_key = Key(Direction, "{0}|{1}|{2}".format(agency_id, route_id, direction_id))
            stop_keys = []
            for stop_el in direction_el.find("stop"):
                stop_id = stop_el.get("id") or stop_el.get("tag")
                stop_keys.append(Key(Stop, "{0}|{1}|{2}|{3}".format(agency_id, route_id, direction_id, stop_id)))
            direction = Direction(
                key = direction_key,
                name = direction_el.get("name"),
                title = direction_el.get("title"),
                agency_key = agency_key,
                route_key = route_key,
                stop_keys = stop_keys)
            direction.put()
            direction_count += 1
            direction_keys.append(direction_key)

        min_lat = route_el.get("minLat") or route_el.get("latMin")
        if min_lat:
            min_lat = Decimal(min_lat)
            if min_lat < agency_min_lat:
                agency_min_lat = min_lat
        min_lng = route_el.get("minLng") or route_el.get("minLon") or route_el.get("lngMin") or route_el.get("lonMin")
        if min_lng:
            min_lng = Decimal(min_lng)
            if min_lng < agency_min_lng:
                agency_min_lng = min_lng
        max_lat = route_el.get("maxLat") or route_el.get("latMax")
        if max_lat:
            max_lat = Decimal(max_lat)
            if max_lat > agency_max_lat:
                agency_max_lat = max_lat
        max_lng = route_el.get("maxLng") or route_el.get("maxLon") or route_el.get("lngMax") or route_el.get("lonMax")
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

        if not min_point or not max_point:
            app.logger.warning("Missing at least one Lat/Lng point for route "+route_id+", agency "+agency_id)

        paths = []
        for path_el in route_el.findall('path'):
            subpaths = []
            for point_el in path_el.findall('point'):
                lat = point_el.get("lat")
                lng = point_el.get("lng") or point_el.get("lon")
                subpaths.append(GeoPt(lat, lng))
            paths.append(subpaths)

        route = Route(
            key = route_key,
            name = route_el.get("name") or route_el.get("title"),
            min_pt = min_point,
            max_pt = max_point,
            paths = paths,
            agency_key = agency_key,
            direction_keys = direction_keys)
        route.put()
        route_count += 1
        route_keys.append(route_key)

    agency = Agency(
        key = agency_key,
        name = agency_el.get("name") or agency_el.get("title"),
        short_name = agency_el.get("shortName") or agency_el.get("shortTitle"),
        region = agency_el.get("region"),
        min_pt = GeoPt(agency_min_lat, agency_min_lng),
        max_pt = GeoPt(agency_max_lat, agency_max_lng),
        route_keys = route_keys)
    agency.put()

    response = dict(
        status = "success",
        agencies = 1,
        routes = route_count,
        directions = direction_count,
        stops = stop_count,
    )
    if direction_association_warning_count:
        response["direction association warnings"] = direction_association_warning_count
    return json.dumps(response)

@app.route('/tasks/nextbus/update')
def fire_agency_deferreds():
    xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(xml)
    except etree.ParseError, e:
        app.logger.error(xml)
        raise e
    if agencies_tree is None:
        # FIXME: handle the case where nextbus is unreachable
        return None
    agency_els = agencies_tree.findall('agency')
    agencies = []
    for agency_el in agency_els:
        agency_id = agency_el.get("id") or agency_el.get("tag")
        if agency_id:
            deferred.defer(update_agency_and_children, agency_id)
            agencies.append(agency_id)

    response = dict(
        status = "agencies enqueued",
        agencies = agencies,
    )
    return json.dumps(response)

