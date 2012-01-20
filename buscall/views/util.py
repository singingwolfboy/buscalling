import datetime
import ndb
from functools import wraps
from simplejson.encoder import JSONEncoder
import simplejson as json
from google.appengine.api.datastore_types import GeoPt
from flask import request, Response

class ExtJSONEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (datetime.datetime, datetime.date, datetime.time)):
            return obj.isoformat()
        elif isinstance(obj, ndb.model.Model):
            return obj._to_dict()
        elif isinstance(obj, ndb.query.QueryIterator):
            return [q for q in obj]
        elif isinstance(obj, GeoPt):
            return (obj.lat, obj.lon)
        return JSONEncoder.default(self, obj)

def render_json(obj, limit=None, offset=None, count=None):
    # TODO: pull limit and offset from QueryIterator, rather than being passed in;
    # calculate count automatically rather than being passed in.

    # get exclusion list
    exclude = request.args.get('exclude') or request.headers.get('X-Exclude')
    if exclude:
        exclusions = [e.strip() for e in exclude.split(",")]
    else:
        exclusions = []
    # get dictionar(ies)
    def process(model):
        if hasattr(model, "_as_url_dict"):
            ret = model._as_url_dict()
        else:
            ret = model
        # remove exclusions
        for exclusion in exclusions:
            if exclusion in ret:
                del ret[exclusion]
        return ret
    if isinstance(obj, (list, tuple, ndb.query.QueryIterator)):
        view_obj = [process(o) for o in obj]
        count = count or len(view_obj)
    else:
        view_obj = process(obj)
    # make response
    resp = Response(json.dumps(view_obj, use_decimal=True, cls=ExtJSONEncoder), mimetype="application/json")
    # include headers
    if limit is not None:
        resp.headers.add("X-Limit", limit)
    if offset is not None:
        resp.headers.add("X-Offset", offset)
    if count is not None:
        resp.headers.add("X-TotalCount", count)
    if exclusions:
        resp.headers.add("X-Excluding", ",".join(exclusions))
    return resp

def api_list(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not 'limit' in kwargs:
            limit = request.args.get('limit') or request.headers.get('X-Limit')
            try:
                kwargs['limit'] = int(limit)
            except (ValueError, TypeError):
                kwargs['limit'] = 20
        if kwargs['limit'] < 1:
            kwargs['limit'] = None

        if not 'offset' in kwargs:
            offset = request.args.get('offset') or request.headers.get('X-Offset')
            try:
                kwargs['offset'] = int(offset)
            except (ValueError, TypeError):
                kwargs['offset'] = 0
        if kwargs['offset'] < 1:
            kwargs['offset'] = None

        return func(*args, **kwargs)
    return wrapper
