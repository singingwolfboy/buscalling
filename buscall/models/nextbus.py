from ndb import model
from google.appengine.api import datastore_types, datastore_errors
from google.appengine.api.datastore_types import GeoPt

class Agency(model.Model):
    name = model.StringProperty()
    short_name = model.StringProperty()
    region = model.StringProperty()
    route_keys = model.KeyProperty(repeated=True)

class PathProperty(model.JsonProperty):
    """
    An NDB property that stores arbitrary lists of GeoPt objects (including lists of
    GeoPts nested inside of lists of GeoPts, to an arbitrary depth).
    """
    def _validate(self, value):
        # if we've already got a GeoPt, it's valid! Return it.
        if isinstance(value, GeoPt):
            return value
        # otherwise, see if we can coerce it
        try:
            return GeoPt(*value)
        except (TypeError, datastore_errors.BadValueError):
            # if we can't coerce it, it might be a list containing other GeoPts,
            # or containing another list recursively...
            if isinstance(value, (list, tuple)):
                return [self._validate(item) for item in value]
            else:
                # something's amiss, raise an error
                raise datastore_errors.BadValueError(
                     "Expected GeoPt, lat/lon pair, or list of GeoPts or lat/lon pairs; "
                     "received %s (a %s)" % (value, datastore_types.typename(value)))

    def _to_base_type(self, value):
        try:
            return (value.lat, value.lon)
        except AttributeError:
            if isinstance(value, basestring):
                # is this a "lat,lon" string?
                # If there are errors, don't catch them
                gp = GeoPt(*value)
                return (gp.lat, gp.lon)
            if isinstance(value, (list, tuple)):
                # is this a lat/lon pair?
                try:
                    gp = GeoPt(*value)
                    return (gp.lat, gp.lon)
                except (TypeError, datastore_errors.BadValueError):
                    return [self._to_base_type(item) for item in value]
            # if not a string or a list/tuple, something is very wrong
            raise datastore_errors.BadValueError(
                 "Expected GeoPt, lat/lon pair, or list of GeoPts or lat/lon pairs; "
                 "received %s (a %s)" % (value, datastore_types.typename(value)))

    def _from_base_type(self, value):
        return self._validate(value)

class Route(model.Model):
    name = model.StringProperty()
    route_key = model.KeyProperty()
    min_pt = model.GeoPtProperty()
    max_pt = model.GeoPtProperty()
    paths = PathProperty()
    direction_keys = model.KeyProperty(repeated=True)


