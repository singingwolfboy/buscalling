from buscall import app
from flask import url_for
from ndb import Key, model
from buscall.models.util import PathProperty
from markupsafe import Markup
from lxml import etree
from .api import get_predictions_xml

resource_uri = Markup("resource_uri")
template_id = Markup("{{id}}")

class Agency(model.Model):
    name = model.StringProperty()
    short_name = model.StringProperty()
    region = model.StringProperty()
    min_pt = model.GeoPtProperty()
    max_pt = model.GeoPtProperty()
    route_keys = model.KeyProperty(repeated=True)
    last_updated = model.DateTimeProperty(auto_now=True)

    @property
    def id(self):
        return self.key.id()

    @property
    def url(self):
        return url_for('agency_detail', agency_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        d['id'] = self.id
        del d['last_updated']
        detail_uri_template = url_for('route_detail', agency_id=self.id, route_id=template_id)
        # unescape mustaches
        detail_uri_template = detail_uri_template.replace("%7B", "{").replace("%7D", "}")
        d['routes'] = dict(
            list_uri = url_for('route_list', agency_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [key.id().split("|")[-1] for key in self.route_keys],
        )
        del d['route_keys']
        return d

class Route(model.Model):
    name = model.StringProperty()
    min_pt = model.GeoPtProperty()
    max_pt = model.GeoPtProperty()
    paths = PathProperty(indexed=False)
    agency_key = model.KeyProperty()
    direction_keys = model.KeyProperty(repeated=True)
    last_updated = model.DateTimeProperty(auto_now=True)

    @property
    def id(self):
        return self.key.id().split("|")[-1]
    @property
    def agency_id(self):
        return self.agency_key.id()

    @property
    def url(self):
        return url_for('route_detail', agency_id=self.agency_id, route_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        d['id'] = self.id
        del d['last_updated']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['agency_key']
        detail_uri_template = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.id, direction_id=template_id)
        # unescape mustaches
        detail_uri_template = detail_uri_template.replace("%7B", "{").replace("%7D", "}")
        d['directions'] = dict(
            list_uri = url_for('direction_list', agency_id=self.agency_id, route_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [key.id().split("|")[-1] for key in self.direction_keys],
        )
        del d['direction_keys']
        return d

class Direction(model.Model):
    name = model.StringProperty()
    altname = model.StringProperty()
    agency_key = model.KeyProperty()
    route_key = model.KeyProperty()
    stop_keys = model.KeyProperty(repeated=True)
    last_updated = model.DateTimeProperty(auto_now=True)

    @property
    def id(self):
        return self.key.id().split("|")[-1]
    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id().split("|")[-1]

    @property
    def url(self):
        return url_for('direction_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        d['id'] = self.id
        del d['last_updated']
        del d['agency_key']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_key']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        detail_uri_template = url_for('stop_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.id, stop_id=template_id)
        # unescape mustaches
        detail_uri_template = detail_uri_template.replace("%7B", "{").replace("%7D", "}")
        d['stops'] = dict(
            list_uri = url_for('stop_list', agency_id=self.agency_id, route_id=self.route_id, direction_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [key.id().split("|")[-1] for key in self.stop_keys],
        )
        del d['stop_keys']
        return d

class Stop(model.Model):
    name = model.StringProperty()
    point = model.GeoPtProperty()
    agency_key = model.KeyProperty()
    route_key = model.KeyProperty()
    direction_key = model.KeyProperty()
    last_updated = model.DateTimeProperty(auto_now=True)

    @property
    def id(self):
        return self.key.id().split("|")[-1]
    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id().split("|")[-1]
    @property
    def direction_id(self):
        return self.direction_key.id().split("|")[-1]

    @property
    def url(self):
        return url_for('stop_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.direction_id, stop_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        d['id'] = self.id
        del d['last_updated']
        del d['agency_key']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_key']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        del d['direction_key']
        d['direction'] = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id)
        d['predictions'] = dict(
            list_uri = url_for('prediction_list', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id, stop_id=self.id),
        )
        return d

class BusPrediction(model.Model):
    agency_key = model.KeyProperty()
    route_key = model.KeyProperty()
    direction_key = model.KeyProperty()
    stop_key = model.KeyProperty()
    trip_id = model.StringProperty() # should this be another KeyProperty? To what?
    minutes = model.IntegerProperty()
    seconds = model.IntegerProperty()
    vehicle = model.StringProperty()
    block = model.StringProperty()
    is_departure = model.BooleanProperty()
    is_affected_by_layover = model.BooleanProperty(default=False)
    is_delayed = model.BooleanProperty()
    slowness = model.IntegerProperty()

    _use_datastore = False # magic variable indicating that this should only
        # be saved to and retrieved from memcache, not the datastore

    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id().split("|")[-1]
    @property
    def direction_id(self):
        return self.direction_key.id().split("|")[-1]
    @property
    def stop_id(self):
        return self.stop_key.id().split("|")[-1]

    @property
    def url(self):
        return url_for('prediction_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.direction_id, stop_id=self.stop_id, trip_id=self.trip_id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        del d['agency_key']
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        del d['route_key']
        d['route'] = url_for('route_detail', agency_id=self.agency_id, route_id=self.route_id)
        del d['direction_key']
        d['direction'] = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id)
        del d['stop_key']
        d['stop'] = url_for('stop_detail', agency_id=self.agency_id,
                route_id=self.route_id, direction_id=self.direction_id, stop_id=self.stop_id)
        return d

    # OVERRIDING standard query() method: returns a list, not a Query object
    @classmethod
    def query(cls, *args, **kwargs):
        ctx = {}
        attributes = ["agency", "route", "direction", "stop", "trip"]
        for node in args:
            name = getattr(node, "_FilterNode__name", None)
            op = getattr(node, "_FilterNode__op", None) or getattr(node, "_FilterNode__opsymbol", None)
            value = getattr(node, "_FilterNode__value", None)
            if not name or not op or not value or op != "=":
                continue
            for attr in attributes:
                attr_id = attr+"_id"
                attr_key = attr+"_key"
                if name == attr_key:
                    key_parts = value.name().split("|")
                    for inner_attr, inner_value in zip(attributes, key_parts):
                        ctx[inner_attr + "_id"] = inner_value
                elif name == attr_id:
                    ctx[attr_id] = value

        # check kwargs overrides
        for attr in attributes:
            attr_id = attr + "_id"
            if attr_id in kwargs:
                ctx[attr_id] = kwargs[attr_id]

        # trip_id should not get passed to get_predictions_xml
        try:
            trip_id = ctx.pop("trip_id")
        except KeyError:
            trip_id = None

        # pull from API
        xml = get_predictions_xml(**ctx)
        try:
            predictions_tree = etree.fromstring(xml)
        except etree.ParseError:
            app.logger.error(xml)
            raise

        # make objects to return
        agency_key = Key(Agency, ctx['agency_id'])
        route_key = Key(Route, "{agency_id}|{route_id}".format(**ctx))
        direction_key = Key(Direction, "{agency_id}|{route_id}|{direction_id}".format(**ctx))
        stop_key = Key(Stop, "{agency_id}|{route_id}|{direction_id}|{stop_id}".format(**ctx))

        def el_to_obj(prediction_el):
            "Convert an lxml-parsed <prediction> element to a BusPrediction object"
            return cls(
                agency_key = agency_key,
                route_key = route_key,
                direction_key = direction_key,
                stop_key = stop_key,
                trip_id = prediction_el.get("tripTag"),
                minutes = int(prediction_el.get("minutes", 0)),
                seconds = int(prediction_el.get("seconds", 0)),
                vehicle = prediction_el.get("vehicle"),
                block = prediction_el.get("block"),
                is_departure = prediction_el.get("isDeparture", "").lower() == "true",
                is_affected_by_layover = prediction_el.get("affectedByLayover", "").lower() == "true",
                is_delayed = prediction_el.get("delayed", "").lower() == "true",
                slowness = int(prediction_el.get("slowness", 0)),
            )

        expr = '/body/predictions/direction/prediction'
        if trip_id:
            expr += '[@tripId="{0}" or @tripTag="{0}"]'.format(trip_id)
        return [el_to_obj(el) for el in predictions_tree.xpath(expr)]

