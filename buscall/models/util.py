from ndb.model import JsonProperty
from google.appengine.api.datastore_types import typename, GeoPt
from google.appengine.api.datastore_errors import BadValueError
from markupsafe import Markup

resource_uri = Markup("resource_uri")
template_id = Markup("{{id}}")

class PathProperty(JsonProperty):
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
        except (TypeError, BadValueError):
            # if we can't coerce it, it might be a list containing other GeoPts,
            # or containing another list recursively...
            if isinstance(value, (list, tuple)):
                return [self._validate(item) for item in value]
            else:
                # something's amiss, raise an error
                raise BadValueError(
                     "Expected GeoPt, lat/lon pair, or list of GeoPts or lat/lon pairs; "
                     "received %s (a %s)" % (value, typename(value)))

    def _to_base_type(self, value):
        try:
            return (value.lat, value.lon)
        except AttributeError:
            if isinstance(value, basestring):
                # is this a "lat,lon" string?
                # If there are errors, don't catch them
                gp = GeoPt(value)
                return (gp.lat, gp.lon)
            if isinstance(value, (list, tuple)):
                # is this a lat/lon pair?
                try:
                    gp = GeoPt(*value)
                    return (gp.lat, gp.lon)
                except (TypeError, BadValueError):
                    return [self._to_base_type(item) for item in value]
            # if not a string or a list/tuple, something is very wrong
            raise BadValueError(
                 "Expected GeoPt, lat/lon pair, or list of GeoPts or lat/lon pairs; "
                 "received %s (a %s)" % (value, typename(value)))

    def _from_base_type(self, value):
        return self._validate(value)
