#!/usr/bin/env python
import requests
from requests import async
from requests.status_codes import _codes
from lxml import etree
from urllib import urlencode
import os
import logging

NEXTBUS_URL = "http://webservices.nextbus.com/service/publicXMLFeed?"
FILE_ROOT = os.path.join(os.path.dirname(__file__), "nextbus_api")

logger = logging.getLogger('cache_nextbus')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
formatter = logging.Formatter()
ch.setFormatter(formatter)
logger.addHandler(ch)

def raw_headers(response):
    headers = response._resp.info().headers
    return "".join([h.replace("\r", "") for h in headers])

def save_response(response, file):
    with open(file, "w") as f:
        code = response.status_code
        desc = _codes[code][0].upper().replace("_", " ")
        http_line = "HTTP/1.1 {code} {desc}\n".format(code=code, desc=desc)
        f.write(http_line)
        f.write(raw_headers(response))
        f.write("\n")
        f.write(response.content.replace("\r", ""))

def handle_agencylist(response):
    logger.info(response.url)
    save_response(response, os.path.join(FILE_ROOT, "agency_list.xml"))
    agencies_tree = etree.fromstring(response.content)
    agency_ids = agencies_tree.xpath('//agency/@tag')
    requests = []
    for agency_id in agency_ids:
        url = NEXTBUS_URL + urlencode({
            "command": "routeList",
            "a": agency_id,
        })
        hooks = {
            "response": get_routelist_handler(agency_id),
        }
        requests.append(async.get(url, hooks=hooks))
    async.map(requests)

def get_routelist_handler(agency_id):
    def handle_routelist(response):
        logger.info(response.url)
        dir = os.path.join(FILE_ROOT, agency_id)
        if not os.path.exists(dir):
            os.mkdir(dir)
        save_response(response, os.path.join(dir, "route_list.xml"))
        routelist_tree = etree.fromstring(response.content)
        route_ids = routelist_tree.xpath('//route/@tag')
        requests = []
        for route_id in route_ids:
            url = NEXTBUS_URL + urlencode({
                "command": "routeConfig",
                "a": agency_id,
                "r": route_id,
            })
            hooks = {
                "response": get_routeconfig_handler(agency_id, route_id),
            }
            requests.append(async.get(url, hooks=hooks))
        async.map(requests)
    return handle_routelist

def get_routeconfig_handler(agency_id, route_id):
    def handle_routeconfig(response):
        logger.info(response.url)
        dir = os.path.join(FILE_ROOT, agency_id, route_id)
        if not os.path.exists(dir):
            os.mkdir(dir)
        save_response(response, os.path.join(dir, "config.xml"))
    return handle_routeconfig

if __name__ == "__main__":
    url = NEXTBUS_URL + urlencode({"command": "agencyList"})
    hooks = dict(response=handle_agencylist)
    requests.get(url, hooks=hooks)
