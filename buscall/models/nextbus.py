from flask import url_for
from ndb import model
from .util import PathProperty
from markupsafe import Markup

resource_uri = Markup("resource_uri")
template_id = Markup("{{id}}")

class Agency(model.Model):
    name = model.StringProperty()
    short_name = model.StringProperty()
    region = model.StringProperty()
    min_pt = model.GeoPtProperty()
    max_pt = model.GeoPtProperty()
    route_keys = model.KeyProperty(repeated=True)

    @property
    def id(self):
        return self.key.id()

    @property
    def url(self):
        return url_for('agency_detail', agency_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        detail_uri_template = url_for('route_detail', agency_id=self.id, route_id=template_id)
        # unescape mustaches
        detail_uri_template = detail_uri_template.replace("%7B", "{").replace("%7D", "}")
        d['routes'] = dict(
            list_uri = url_for('route_list', agency_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [key.id() for key in self.route_keys],
        )
        del d['route_keys']
        d['latMin'] = self.min_pt.lat
        d['lngMin'] = self.min_pt.lng
        d['latMax'] = self.max_pt.lat
        d['lngMax'] = self.max_pt.lng
        return d

class Route(model.Model):
    name = model.StringProperty()
    min_pt = model.GeoPtProperty()
    max_pt = model.GeoPtProperty()
    paths = PathProperty()
    agency_key = model.KeyProperty()
    direction_keys = model.KeyProperty(repeated=True)

    @property
    def id(self):
        return self.key.id()
    @property
    def agency_id(self):
        return self.agency_key.id()

    @property
    def url(self):
        return url_for('route_detail', agency_id=self.agency_id, route_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
        d['agency'] = url_for('agency_detail', agency_id=self.agency_id)
        detail_uri_template = url_for('direction_detail', agency_id=self.agency_id,
                route_id=self.id, direction_id=template_id)
        # unescape mustaches
        detail_uri_template = detail_uri_template.replace("%7B", "{").replace("%7D", "}")
        d['directions'] = dict(
            list_uri = url_for('direction_list', agency_id=self.agency_id, route_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [key.id() for key in self.direction_keys],
        )
        del d['direction_key']
        d['latMin'] = self.min_pt.lat
        d['lngMin'] = self.min_pt.lng
        d['latMax'] = self.max_pt.lat
        d['lngMax'] = self.max_pt.lng
        return d

class Direction(model.Model):
    name = model.StringProperty()
    title = model.StringProperty()
    agency_key = model.KeyProperty()
    route_key = model.KeyProperty()
    stop_keys = model.KeyProperty(repeated=True)

    @property
    def id(self):
        return self.key.id()
    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id()

    @property
    def url(self):
        return url_for('direction_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.id)

    def _as_url_dict(self):
        d = self._to_dict()
        d[resource_uri] = self.url
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
            ids = [key.id() for key in self.stop_keys],
        )
        del d['stop_keys']
        return d

class Stop(model.Model):
    name = model.StringProperty()
    point = model.GeoPtProperty()
    agency_key = model.KeyProperty()
    route_key = model.KeyProperty()
    direction_key = model.KeyProperty()

    @property
    def id(self):
        return self.key.id()
    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id()
    @property
    def direction_id(self):
        return self.direction_key.id()

    @property
    def url(self):
        return url_for('stop_detail', agency_id=self.agency_id, route_id=self.route_id,
                direction_id=self.direction_id, stop_id=self.id)

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
    departure = model.StringProperty()
    affected_by_layover = model.BooleanProperty(default=False)
    delayed = model.StringProperty()
    slowness = model.StringProperty()

    _use_datastore = False # magic variable indicating that this should only
        # be saved to and retrieved from memcache, not the datastore

    @property
    def agency_id(self):
        return self.agency_key.id()
    @property
    def route_id(self):
        return self.route_key.id()
    @property
    def direction_id(self):
        return self.direction_key.id()
    @property
    def stop_id(self):
        return self.stop_key.id()

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

