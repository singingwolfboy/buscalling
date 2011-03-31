from buscall import app
from flask import render_template
from google.appengine.api import urlfetch, memcache
from xml.etree import ElementTree
import logging

@app.route('/')
def hello():
    return render_template('hello.html')

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?a=mbta"

@app.route('/routes')
def index_routes():
    "Asynchronously fetch the list of supported MBTA routes."
    # check memcache first
    routes = memcache.get("index_routes")
    if routes is not None:
        logging.info("Retrieved index_routes from memcache")
    else:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=routeList"
        urlfetch.make_fetch_call(rpc, url)
        # Here we could do things asynchronously, but in this case, 
        # we need the result of the RPC before we can do anything else.
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("index_routes RPC returned status code %s" % result.status_code)
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)

        body = ElementTree.fromstring(result.content)
        routes = [route.attrib for route in body.findall('route')]

        saved = memcache.set("index_routes", routes, 3600)
        if not saved:
            logging.error("Memcache set failed for index_routes")
    
    return render_template('routes/index.html', routes=routes)

@app.route('/routes/<int:route_id>')
def show_route(route_id):
    route = memcache.get("show_route|%d" % route_id)
    if not route:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=routeConfig&r=%d" % route_id
        urlfetch.make_fetch_call(rpc, url)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("show_route %d RPC returned status code %s" % (route_id, result.status_code))
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)
        
        tree = ElementTree.fromstring(result.content)
        route = parse_route_xml(tree)
        # stick ID in, just for good measure
        route['id'] = route_id

        saved = memcache.set("show_route|%d" % route_id, route, 3600)
        if not saved:
            logging.error("Memcache set failed for show_route %d" % route_id)
    
    return render_template('routes/show.html', route=route)

def parse_route_xml(tree):
    routeElem = tree.find('route')
    # basic route attributes
    route = routeElem.attrib

    # detailed info about stops
    stops = {}
    for stop in routeElem.findall("stop"):
        stop_info = stop.attrib
        stop_id = stop_info['tag']
        del stop_info['tag']
        stops[stop_id] = stop_info
    route['stops'] = stops

    # directions (inbound, outbound)
    directions = {}
    for direction in routeElem.findall('direction'):
        dir_info = direction.attrib
        dir_id = dir_info['tag']
        del dir_info['tag']
        # make list of stops
        dir_info['stops'] = [stop.get('tag') for stop in direction.findall('stop')]
        directions[dir_id] = dir_info
    route['directions'] = directions
    
    # path of lat/long points
    route_path = []
    for path in routeElem.findall('path'):
        segment = [(point.get('lat'), point.get('lon')) 
            for point in path.findall('point')]
        route_path.append(segment)
    route['path'] = route_path

    return route





        
