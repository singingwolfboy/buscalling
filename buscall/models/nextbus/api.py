from buscall import app
from flask import g, Response
from google.appengine.api import urlfetch
import logging
import re
import time
import random
from urllib import urlencode
from buscall import cache
import simplejson as json
from lxml import etree
from functools import wraps

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

def retry_nextbus_api(retries):
    def factory(func):
        @wraps(func)
        def decorator(*args, **kwargs):
            last_err = None
            for n in range(0, retries):
                try:
                    return func(*args, **kwargs)
                except NextbusError, e:
                    if not e.retry:
                        raise e
                    last_err = e
                    # exponential backoff
                    time.sleep((2**n) + (random.randint(0, 1000) / 1000))
            if retries < 2:
                raise last_err
            raise NextbusError("Failed after {retries} attempts. Error was: {message}".format(
                retries=retries, message=last_err.message), retry=last_err.retry)
        return decorator
    return factory

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
    except etree.ParseError, e:
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
@retry_nextbus_api(5)
def get_agencylist_xml(retries=5):
    return get_nextbus_xml({
        "command": "agencyList",
    })

@cache.memoize(timeout=HOUR)
@retry_nextbus_api(5)
def get_routelist_xml(agency_id):
    return get_nextbus_xml({
        "a": agency_id,
        "command": "routeList",
    })

@cache.memoize(timeout=HOUR)
@retry_nextbus_api(5)
def get_route_xml(agency_id, route_id):
    return get_nextbus_xml({
        "a": agency_id,
        "r": route_id,
        "command": "routeConfig",
    })

@cache.memoize(timeout=SHORT)
@retry_nextbus_api(5)
def get_predictions_xml(agency_id, route_id, direction_id, stop_id):
    "Each physical stop has multiple IDs, depending on the bus direction."
    return get_nextbus_xml({
        "a": agency_id,
        "r": route_id,
        "d": direction_id,
        "s": stop_id,
        "command": "predictions",
    })

