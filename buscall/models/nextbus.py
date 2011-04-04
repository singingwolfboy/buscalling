from google.appengine.api import urlfetch, memcache
from xml.etree import ElementTree as etree
import logging

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?a=mbta"

def get_all_routes():
    routes = memcache.get("index_routes")
    if routes is None:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=routeList"
        urlfetch.make_fetch_call(rpc, url)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("index_routes RPC returned status code %s" % result.status_code)
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)

        tree = etree.fromstring(result.content)
        routes = parse_index_xml(tree)

        saved = memcache.set("index_routes", routes, 3600)
        if not saved:
            logging.error("Memcache set failed for index_routes")
    return routes
   
def parse_index_xml(tree):
    return [clean_booleans(route.attrib) for route in tree.findall('route')]

def get_route(route_id):
    route = memcache.get("show_route|%s" % route_id)
    if route is None:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=routeConfig&r=%s" % route_id
        urlfetch.make_fetch_call(rpc, url)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("show_route %s RPC returned status code %s" % (route_id, result.status_code))
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)
        
        tree = etree.fromstring(result.content)
        route = parse_route_xml(tree)
        # stick ID in, just for good measure
        route['id'] = route_id

        saved = memcache.set("show_route|%s" % route_id, route, 3600)
        if not saved:
            logging.error("Memcache set failed for show_route %s" % route_id)
    return route

def parse_route_xml(tree):
    routeElem = tree.find('route')
    # basic route attributes
    route = clean_booleans(routeElem.attrib)

    # detailed info about stops
    stops = {}
    for stop in routeElem.findall("stop"):
        stop_info = stop.attrib
        stop_id = stop_info['tag']
        del stop_info['tag']
        stops[stop_id] = clean_booleans(stop_info)
    route['stops'] = stops

    # directions (inbound, outbound)
    directions = {}
    for direction in routeElem.findall('direction'):
        dir_info = direction.attrib
        dir_id = dir_info['tag']
        del dir_info['tag']
        # make list of stops
        dir_info['stops'] = [stop.get('tag') for stop in direction.findall('stop')]
        directions[dir_id] = clean_booleans(dir_info)
    route['directions'] = directions
    
    # path of lat/long points
    route_path = []
    for path in routeElem.findall('path'):
        segment = [(point.get('lat'), point.get('lon')) 
            for point in path.findall('point')]
        route_path.append(segment)
    route['path'] = route_path

    return route

def get_route_directions(route):
    directions = memcache.get("show_route|%s|directions" % route['id'])
    if directions is None:
        directions = []
        for dir_id, direc in route['directions'].items():
            stops = []
            for stop_id in direc['stops']:
                stop_info = route['stops'][stop_id]
                stop_info['id'] = stop_id
                stops.append(stop_info)
            
            directions.append({
                'title': direc['title'],
                'id': dir_id,
                'stops': stops,
            })
        
        saved = memcache.set("show_route|%s|directions" % route['id'], directions, 3600)
        if not saved:
            logging.error("Memcache set failed for show_route %s directions" % route['id'])
    return directions


def get_prediction(route_id, stop_id):
    "Each physical stop has multiple IDs, depending on the bus direction."
    prediction = memcache.get("predict|%s|%s" % (route_id, stop_id))
    if prediction is None:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=predictions&r=%s&s=%s" % (route_id, stop_id)
        urlfetch.make_fetch_call(rpc, url)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("predict_for_stop %s, %s RPC returned status code %s" % (route_id, stop_id, result.status_code))
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)
        
        tree = etree.fromstring(result.content)
        prediction = parse_predict_xml(tree)

        saved = memcache.set("predict|%s|%s" % (route_id, stop_id), prediction, 20)
        if not saved:
            logging.error("Memcache set failed for predict_for_stop %s|%s" % (route_id, stop_id))
    return prediction

def parse_predict_xml(tree):
    prediction_el = tree.find('predictions')
    direction_el = prediction_el.find('direction')
    predictions_el = direction_el.findall('prediction')
    buses, epoch_time = parse_predictions_element(predictions_el)

    return {
        'route_id':     prediction_el.get('routeTag'),
        'route_title':  prediction_el.get('routeTitle'),
        'stop_id':      prediction_el.get('stopTag'),
        'stop_title':   prediction_el.get('stopTitle'),
        'direction':    direction_el.get('title'),
        'buses':        buses,
        'epoch_time':   epoch_time
    }

def parse_predictions_element(predictions_el):
    buses = []
    for prediction_el in predictions_el:
        p = prediction_el.attrib
        epoch_time = p['epochTime']
        # strip off what we don't care about
        del p['dirTag']
        del p['epochTime']
        buses.append(clean_booleans(p))
    return buses, epoch_time

def clean_booleans(d):
    for key in d.keys():
        try:
            val = d[key].lower()
            if val == 'true' or val == 't':
                d[key] = True
            elif val == 'false' or val == 'f':
                d[key] = False
        except AttributeError:
            pass
    return d