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
    if routes is None:
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

@app.route('/routes/<route_id>')
def show_route(route_id):
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
        
        tree = ElementTree.fromstring(result.content)
        route = parse_route_xml(tree)
        # stick ID in, just for good measure
        route['id'] = route_id

        saved = memcache.set("show_route|%s" % route_id, route, 3600)
        if not saved:
            logging.error("Memcache set failed for show_route %s" % route_id)
    
    # organize stop/direction info
    directions = memcache.get("show_route|%s|directions" % route_id)
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
        
        saved = memcache.set("show_route|%s|directions" % route_id, directions, 3600)
        if not saved:
            logging.error("Memcache set failed for show_route %s directions" % route_id)

    return render_template('routes/show.html', route=route, directions=directions)

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

@app.route('/predict/<route_id>/<stop_id>')
@app.route('/predict/<route_id>/<stop_id>/<dir_id>')
def predict_for_stop(route_id, stop_id, dir_id=None):
    prediction = memcache.get("predict|%s|%s|%s" % (route_id, stop_id, dir_id))
    if prediction is None:
        rpc = urlfetch.create_rpc()
        url = RPC_URL + "&command=predictions&r=%s&s=%s" % (route_id, stop_id)
        if dir_id:
            url += "&d=%s" % dir_id
        urlfetch.make_fetch_call(rpc, url)
        try:
            result = rpc.get_result()
            if result.status_code != 200:
                logging.error("predict_for_stop %s, %s, %s RPC returned status code %s" % (route_id, stop_id, dir_id, result.status_code))
        except urlfetch.DownloadError:
            logging.error("Download error: " + url)
        
        tree = ElementTree.fromstring(result.content)
        # do work here
        prediction = None

        saved = memcache.set("predict|%s|%s|%s" % (route_id, stop_id, dir_id), prediction, 20)
        if not saved:
            logging.error("Memcache set failed for predict_for_stop %s|%s|%s" % (route_id, stop_id, dir_id))
    
    return render_template('routes/predict.html', prediction=prediction)
