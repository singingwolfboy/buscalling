import datetime
import random
from buscall import app
from buscall.util import DAYS_OF_WEEK
from flask import redirect, url_for
from google.appengine.api.datastore_types import GeoPt
from buscall.models.nextbus import Agency, Route, Direction, Stop
from buscall.models.listener import BusListener
from ndb import Key
from decimal import Decimal
from lxml import etree
import simplejson as json
from buscall.models.nextbus.api import NextbusError
from buscall.models.nextbus.api import get_agencylist_xml, get_routelist_xml, get_route_xml
from google.appengine.api import taskqueue

@app.route('/tasks/poll')
def poll(dt=None):
    """
    This function is the workhorse of the whole application. When called,
    it checks the current time, pulls listeners from the datastore that are
    currently active, and then polls the bus routes for those listeners.
    This function is designed to be run once a minute (or more!) through cron.
    """
    if dt is None:
        dt = datetime.datetime.utcnow()  # current time

    # get all currently active listeners
    weekday = DAYS_OF_WEEK[dt.weekday()]
    listeners = BusListener.query(
            getattr(BusListener, weekday) == True,
            BusListener.start <= dt.time(),
            BusListener.scheduled_notifications.has_executed == False,
            BusListener.enabled == True)
    for listener in listeners:
        predictions = listener.get_predictions()
        for scheduled_notification in listener.scheduled_notifications:
            for prediction in predictions:
                if scheduled_notification.minutes_before == prediction.minutes:
                    scheduled_notification.notify(listener, prediction)

    return redirect(url_for("lander"), 303)

@app.route('/tasks/reset_seen_flags')
def reset_seen_flags():
    listeners = BusListener.query(BusListener.scheduled_notifications.has_executed == True)
    for listener in listeners:
        if listener.recur:
            # reset the "has_executed" flag on all scheduled notifications
            for scheduled_notification in listener.scheduled_notifications:
                scheduled_notification.has_executed = False
            listener.put()
        else:
            # the listener has run, and it shouldn't run again, so delete it
            listener.delete()
    return redirect(url_for("lander"), 303)

@app.route('/tasks/nextbus/update/<agency_id>', methods=["POST"])
def update_agency_and_children(agency_id):
    return load_nextbus_entities_for_agency(agency_id, routes=True, directions=True, stops=True)

def load_nextbus_entities_for_agency(agency_id, routes=True, directions=True, stops=True):
    """
    Insert entities into datastore based on the information from Nextbus.
    This function is designed to run both as a background task on the live
    site, and as a utility function for testing (in which case it should use
    the cached Nextbus responses on disk rather than actually contacting
    www.nextbus.com). This function requires a single agency_id as a string,
    but for the other parameters, passing different values indicates different
    behavior:

    * True means load all the entities we can find for that entity type, given
      the parents we have. Passing routes=True means load all routes for
      this agency. Passing passing directions=True with routes="70" means
      load all directions within the 70 bus route only.
    * a list of strings means only load the entities with the given ids.
      Passing routes=["70"] means only load the 70 bus route.
      Passing routes=["70", "556"] means only load the 70 bus and the 556
      bus routes.
    * an integer means to load up to that many entities, and no more, per parent.
      Precisely which entities get loaded is undefined. If the parent defines
      fewer entities than the integer specified, all of them are loaded.
      For example, if we pass routes=["70", "556"], directions=2, and the 70 bus
      defines 5 directions while the 556 bus defines 1, then 2 directions for
      the 70 bus will be loaded, and the single direction on the 556 bus will
      also be loaded. Note that passing 0 is functionally identical to passing
      False.
    * False means to not load any entities of the given type. This halts processing:
      if you define routes=False, then no directions or stops will be loaded,
      regardless of what arguments you specify for them.

    For this function, all arguments default to True, since that's what we want
    when running this function in production on the task queue.
    """
    stop_count = 0
    direction_count = 0
    route_count = 0
    direction_association_warning_count = 0
    al_xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(al_xml)
    except etree.ParseError:
        app.logger.error(al_xml)
        raise
    expr = '//agency[@id="{id}" or @tag="{id}"][1]'.format(id=agency_id)
    agency_els = agencies_tree.xpath(expr)
    try:
        agency_el = agency_els[0]
    except IndexError:
        raise NextbusError("Invalid agency: {0}".format(agency_id), retry=False)
    agency_key = Key(Agency, agency_id)
    agency_min_lat = 90
    agency_min_lng = 180
    agency_max_lat = -90
    agency_max_lng = -180
    route_keys = []
    rl_xml = get_routelist_xml(agency_id)
    try:
        routelist_tree = etree.fromstring(rl_xml)
    except etree.ParseError:
        app.logger.error(rl_xml)
        raise

    # check limitations for unit tests
    if routes:
        route_stub_els = routelist_tree.findall('route')
        if routes is True:
            pass
        elif isinstance(routes, int):
            route_stub_els = route_stub_els[0:routes]
        elif isinstance(routes, (list, tuple)):
            def on_list(route_stub_el):
                route_id = route_stub_el.get("id") or route_stub_el.get("tag")
                return route_id in routes
            route_stub_els = filter(on_list, route_stub_els)
    else:
        route_stub_els = []

    for route_stub_el in route_stub_els:
        route_id = route_stub_el.get("id") or route_stub_el.get("tag")
        route_key = Key(Route, "{0}|{1}".format(agency_id, route_id))
        rc_xml = get_route_xml(agency_id, route_id)
        try:
            route_tree = etree.fromstring(rc_xml)
        except etree.ParseError:
            app.logger.error(rc_xml)
            raise
        route_el = route_tree.find('route')

        # check limitations for unit tests
        if stops:
            stop_els = route_tree.xpath('//route/stop')
            if stops is True:
                pass
            elif isinstance(stops, int):
                stop_els = stop_els[0:stops]
            elif isinstance(stops, (list, tuple)):
                def on_list(stop_el):
                    stop_id = stop_el.get("id") or stop_el.get("tag")
                    return stop_id in stops
                stop_els = filter(on_list, stop_els)
        else:
            stop_els = []

        for stop_el in stop_els:
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
            stop.put_async()
            stop_count += 1

        # check limitations for unit tests
        if directions:
            direction_els = route_tree.xpath('//route/direction')
            if directions is True:
                pass
            elif isinstance(directions, int):
                direction_els = direction_els[0:directions]
            elif isinstance(directions, (list, tuple)):
                def on_list(direction_el):
                    direction_id = direction_el.get("id") or direction_el.get("tag")
                    return direction_id in directions
                direction_els = filter(on_list, direction_els)
        else:
            direction_els = []

        direction_keys = []
        for direction_el in direction_els:
            direction_id = direction_el.get("id") or direction_el.get("tag")
            direction_key = Key(Direction, "{0}|{1}|{2}".format(agency_id, route_id, direction_id))
            stop_keys = []
            for stop_el in direction_el.findall("stop"):
                stop_id = stop_el.get("id") or stop_el.get("tag")
                stop_keys.append(Key(Stop, "{0}|{1}|{2}|{3}".format(agency_id, route_id, direction_id, stop_id)))
            # Nextbus uses "title" as the main name for a direction, and "name" as a secondary:
            # we use "name" as the main name, and "altname" as a secondary, which makes more sense
            direction = Direction(
                key = direction_key,
                name = direction_el.get("title"), # note the switcheroo!
                altname = direction_el.get("name"),
                agency_key = agency_key,
                route_key = route_key,
                stop_keys = stop_keys)
            direction.put_async()
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
        route.put_async()
        route_count += 1
        route_keys.append(route_key)

    if agency_min_lat < 90 and agency_min_lng < 180:
        min_pt = GeoPt(agency_min_lat, agency_min_lng)
    else:
        min_pt = None
    if agency_max_lat > -90 and agency_max_lng > -180:
        max_pt = GeoPt(agency_max_lat, agency_max_lng)
    else:
        max_pt = None
    agency = Agency(
        key = agency_key,
        name = agency_el.get("name") or agency_el.get("title"),
        short_name = agency_el.get("shortName") or agency_el.get("shortTitle"),
        region = agency_el.get("region") or agency_el.get("regionTitle"),
        min_pt = min_pt,
        max_pt = max_pt,
        route_keys = route_keys)
    agency.put_async().get_result()

    response = {
        "status": "success",
        "agencies": 1,
        "routes": route_count,
        "directions":  direction_count,
        "stops": stop_count,
        "association warnings": direction_association_warning_count,
    }
    app.logger.info(response)
    return json.dumps(response)

@app.route('/tasks/nextbus/update', methods=["POST"])
def add_agency_update_tasks():
    xml = get_agencylist_xml()
    try:
        agencies_tree = etree.fromstring(xml)
    except etree.ParseError:
        app.logger.error(xml)
        raise
    if agencies_tree is None:
        # FIXME: handle the case where nextbus is unreachable
        return None
    agency_els = agencies_tree.findall('agency')
    agencies = []
    for agency_el in agency_els:
        agency_id = agency_el.get("id") or agency_el.get("tag")
        if agency_id:
            taskqueue.add(name=agency_id,
                countdown=random.randint(0, 120),  # wait up to two minutes
                url=url_for('update_agency_and_children', agency_id=agency_id))
            agencies.append(agency_id)

    response = dict(
        status = "agencies enqueued",
        agencies = agencies,
    )
    return json.dumps(response)

