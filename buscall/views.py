from buscall import app
from flask import render_template
from google.appengine.api import urlfetch, memcache
from xml.etree import ElementTree
import logging

@app.route('/')
def hello():
    return render_template('hello.html')

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?a=mbta"

@app.route('/routes')
def index_routes():
    routes = get_all_routes()
    return render_template('routes/index.html', routes=routes)

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

        tree = ElementTree.fromstring(result.content)
        routes = parse_index_xml(tree)

        saved = memcache.set("index_routes", routes, 3600)
        if not saved:
            logging.error("Memcache set failed for index_routes")
    return routes

def parse_index_xml(tree):
    return [clean_booleans(route.attrib) for route in tree.findall('route')]

@app.route('/routes/<route_id>')
def show_route(route_id):
    route = get_route(route_id)
    directions = get_route_directions(route)
    return render_template('routes/show.html', route=route, directions=directions)

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
        
        tree = ElementTree.fromstring(result.content)
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


@app.route('/predict/<route_id>/<stop_id>')
@app.route('/predict/<route_id>/<stop_id>/<dir_id>')
def predict_for_stop(route_id, stop_id, dir_id=None):
    route = get_route(route_id)
    stop = route['stops'][stop_id]
    predictions = get_predictions(route_id, stop_id, dir_id)
    return render_template('routes/predict.html', route=route, stop=stop, predictions=predictions)

def get_predictions(route_id, stop_id, dir_id=None):
    predictions = memcache.get("predict|%s|%s|%s" % (route_id, stop_id, dir_id))
    if predictions is None:
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
        predictions = parse_predict_xml(tree)

        saved = memcache.set("predict|%s|%s|%s" % (route_id, stop_id, dir_id), predictions, 20)
        if not saved:
            logging.error("Memcache set failed for predict_for_stop %s|%s|%s" % (route_id, stop_id, dir_id))
    return predictions

def parse_predict_xml(tree):
    predictions = {}
    predElem = tree.find('predictions')
    directions = predElem.findall('direction')
    for direction in directions:
        firstPred = direction.find('prediction')
        pred_dir_id = firstPred.get('dirTag')
        epochTime = firstPred.get('epochTime')

        predList = []
        for prediction in direction.findall('prediction'):
            p = prediction.attrib
            # strip off what we don't care about
            del p['dirTag']
            del p['epochTime']
            predList.append(clean_booleans(p))
        
        predictions[pred_dir_id] = {
            'epochTime': int(epochTime),
            'predictions': predList,
        }
    
    return predictions

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
