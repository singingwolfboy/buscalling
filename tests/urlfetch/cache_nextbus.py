#!/usr/bin/env python
import requests
from requests import async
from requests.status_codes import _codes
from lxml import etree
from urllib import urlencode
import os
import logging
import argparse

NEXTBUS_URL = "http://webservices.nextbus.com/service/publicXMLFeed?"
FILE_ROOT = os.path.join(os.path.dirname(__file__), "nextbus_api")

logger = logging.getLogger('cache_nextbus')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter()
ch.setFormatter(formatter)
logger.addHandler(ch)

def raw_headers(response):
    return "\n".join(["{k}: {v}".format(k=k, v=v) for k, v in response.headers.items()])

def save_response(response, file):
    with open(file, "w") as f:
        code = response.status_code
        desc = _codes[code][0].upper().replace("_", " ")
        http_line = "HTTP/1.1 {code} {desc}\n".format(code=code, desc=desc)
        f.write(http_line)
        f.write(raw_headers(response))
        f.write("\n\n")
        f.write(response.content.replace("\r", ""))

def handle_error(tree, url, func):
    error = tree.find('Error')
    if error is None:
        return False
    retry = error.attrib.get('shouldRetry')
    if retry is None:
        retry = False
    if not isinstance(retry, bool):
        retry = retry.lower() == "true"
    if not retry:
        raise Exception(error.text.strip())
    async.map([async.get(url, hooks=dict(response=func))])
    return True

def handle_agencylist(response):
    logger.info(response.url)
    agencies_tree = etree.fromstring(response.content)
    has_error = handle_error(agencies_tree, response.url, handle_agencylist)
    if has_error:
        return False
    save_response(response, os.path.join(FILE_ROOT, "agency_list.xml"))
    agency_ids = agencies_tree.xpath('//agency/@tag')
    reqs = []
    for agency_id in agency_ids:
        url = NEXTBUS_URL + urlencode({
            "command": "routeList",
            "a": agency_id,
        })
        hooks = {
            "response": get_routelist_handler(agency_id),
        }
        reqs.append(async.get(url, hooks=hooks))
    async.map(reqs)

def get_routelist_handler(agency_id):
    def handle_routelist(response):
        logger.info(response.url)
        dir = os.path.join(FILE_ROOT, agency_id)
        if not os.path.exists(dir):
            os.mkdir(dir)
        routelist_tree = etree.fromstring(response.content)
        has_error = handle_error(routelist_tree, response.url, get_routelist_handler(agency_id))
        if has_error:
            return False
        save_response(response, os.path.join(dir, "route_list.xml"))
        route_ids = routelist_tree.xpath('//route/@tag')
        reqs = []
        for route_id in route_ids:
            url = NEXTBUS_URL + urlencode({
                "command": "routeConfig",
                "a": agency_id,
                "r": route_id,
            })
            hooks = {
                "response": get_routeconfig_handler(agency_id, route_id),
            }
            reqs.append(async.get(url, hooks=hooks))
        async.map(reqs)
    return handle_routelist

def get_routeconfig_handler(agency_id, route_id):
    def handle_routeconfig(response):
        logger.info(response.url)
        routeconfig_tree = etree.fromstring(response.content)
        has_error = handle_error(routeconfig_tree, response.url, get_routeconfig_handler(agency_id, route_id))
        if has_error:
            return False
        dir = os.path.join(FILE_ROOT, agency_id, route_id)
        if not os.path.exists(dir):
            os.mkdir(dir)
        save_response(response, os.path.join(dir, "config.xml"))
    return handle_routeconfig

def get_predictions_handler(agency_id, route_id, direction_id="", stop_id=""):
    def handle_predictions(response):
        logger.info(response.url)
        predictions_tree = etree.fromstring(response.content)
        has_error = handle_error(predictions_tree, response.url,
                get_predictions_handler(agency_id, route_id, direction_id, stop_id))
        if has_error:
            return False
        dir = os.path.join(FILE_ROOT, agency_id, route_id)
        if not os.path.exists(dir):
            os.mkdir(dir)
        save_response(response, os.path.join(dir, stop_id + ".xml"))
    return handle_predictions

def get_parser():
    parser = argparse.ArgumentParser(description="cache Nextbus responses for testing")
    parser.add_argument('-a', '--agency')
    parser.add_argument('-r', '--route')
    parser.add_argument('-d', '--direction')
    parser.add_argument('-s', '--stop', help="Get current predictions for stop")
    parser.add_argument('positionals', help=argparse.SUPPRESS, nargs="*")
    return parser

def main():
    args = get_parser().parse_args()
    # deal with positionals
    if len(args.positionals) > 0 and not args.agency:
        args.agency = args.positionals[0]
    if len(args.positionals) > 1 and not args.route:
        args.route = args.positionals[1]
    if len(args.positionals) > 2 and not args.direction:
        args.direction = args.positionals[2]
    if len(args.positionals) > 3 and not args.stop:
        args.stop = args.positionals[3]

    if args.agency and args.route and args.stop: # direction isn't needed
        url_args = {
            "command": "predictions",
            "a": args.agency,
            "r": args.route,
            "s": args.stop,
        }
        if args.direction:
            url_args["d"] = args.direction
        url = NEXTBUS_URL + urlencode(url_args)
        hooks = dict(response=get_predictions_handler(args.agency,
            args.route, args.direction, args.stop))
    elif args.agency and args.route:
        url = NEXTBUS_URL + urlencode({
            "command": "routeConfig",
            "a": args.agency,
            "r": args.route,
        })
        hooks = dict(response=get_routeconfig_handler(args.agency, args.route))
    elif args.agency:
        url = NEXTBUS_URL + urlencode({
            "command": "routeList",
            "a": args.agency,
        })
        hooks = dict(response=get_routelist_handler(args.agency))
    else:
        url = NEXTBUS_URL + urlencode({"command": "agencyList"})
        hooks = dict(response=handle_agencylist)
    requests.get(url, hooks=hooks)

if __name__ == "__main__":
    main()
