import os
import os.path
import sys
import unittest
import simplejson as json
from httplib import HTTPResponse
from StringIO import StringIO
from urlparse import urlparse
from google.appengine.api import urlfetch_stub
from google.appengine.api.capabilities import capability_stub
from google.appengine.ext import testbed
from google.appengine.api.urlfetch_stub import \
  _API_CALL_DEADLINE, _API_CALL_VALIDATE_CERTIFICATE_DEFAULT
import buscall
from ndb import Key
from buscall.models.user import User
from buscall.models.nextbus import Agency, Route, Direction, Stop
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs


PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
URLFETCH_ROOT = os.path.join(PROJECT_ROOT, "tests", "urlfetch")
LIB_ROOT = os.path.join(PROJECT_ROOT, "lib")
sys.path.insert(0, LIB_ROOT)

# need to set AUTH_DOMAIN before we can create User objects,
# so just do this on import
if not 'AUTH_DOMAIN' in os.environ:
    os.environ['AUTH_DOMAIN'] = 'gmail.com'

# from http://pythonwise.blogspot.com/2010/02/parse-http-response.html
class FakeSocket(StringIO):
    def makefile(self, *args, **kw):
        return self

def httpparse(fp):
    try:
        contents = fp.read()
    except AttributeError:
        contents = fp
    socket = FakeSocket(contents)
    response = HTTPResponse(socket)
    response.begin()
    return response
# end http://pythonwise.blogspot.com/2010/02/parse-http-response.html

class CustomURLFetchServiceStub(urlfetch_stub.URLFetchServiceStub):
    def __init__(self, root="urlfetch",  *args, **kwargs):
        super(CustomURLFetchServiceStub, self).__init__(*args, **kwargs)
        self.root = root
        self.history = []
        self.responses = {}

    def _get_response(self, url, payload):
        parts = urlparse(url)
        if parts.netloc == "webservices.nextbus.com":
            rel_path = self._get_nextbus_path(parse_qs(parts.query))
            if not rel_path: return None
            return open(rel_path)
            # return open(os.path.join(os.path.dirname(__file__), rel_path))
        elif parts.netloc == "api.twilio.com":
            return self._get_twilio_response(parse_qs(payload))

        return None
  
    def _get_nextbus_path(self, params):
        try:
            command = params['command'][0]
        except KeyError:
            return os.path.join(self.root, "nextbus_api", "no_params.xml")
        if command == "agencyList":
            return os.path.join(self.root, "nextbus_api", "agency_list.xml")
        if command == "routeList":
            return os.path.join(self.root, "nextbus_api", params['a'][0], "route_list.xml")
        elif command == "routeConfig":
            return os.path.join(self.root, "nextbus_api", params['a'][0], params['r'][0], "config.xml")
        elif command == "predictions":
            return os.path.join(self.root, "nextbus_api", params['a'][0], params['r'][0], params['s'][0]+".xml")
        return None
  
    def _get_twilio_response(self, params):
        return json.dumps({
          "to": params["To"][0],
          "from": params["From"][0],
          "sid": "1234567890",
        })
  
    def _RetrieveURL(self, url, payload, method, headers, request, response,
                 follow_redirects=True, deadline=_API_CALL_DEADLINE,
                 validate_certificate=_API_CALL_VALIDATE_CERTIFICATE_DEFAULT):
        resp = self._get_response(url, payload)

        if not resp:
          raise testbed.Error("unknown URL: "+url)

        http_resp = httpparse(resp)
        content = http_resp.fp.read()
        response.set_statuscode(http_resp.status)
        response.set_content(content)
        self.history.append(url)
        self.responses[url] = content

CAPABILITIES_SERVICE_NAME = 'capability_service'

class CustomTestbed(testbed.Testbed):
    def init_custom_urlfetch_stub(self, enable=True, root=None):
        """
        OVERRIDES the standard urlfetch stub. Call either this function
        or the init_urlfetch_stub function -- NOT BOTH.

        Args:
          root: a path to the root of the file tree to serve files out of
        """
        if not enable:
            self._disable_stub(testbed.URLFETCH_SERVICE_NAME)
            return
        stub = CustomURLFetchServiceStub(root)
        self._register_stub(testbed.URLFETCH_SERVICE_NAME, stub)

    def init_capability_stub(self, enable=True):
        """Enable the capabilities stub.

        Args:
          enable: True, if the fake service should be enabled, False if real
                service should be disabled.
        """
        if not enable:
            self._disable_stub(CAPABILITIES_SERVICE_NAME)
            return
        stub = capability_stub.CapabilityServiceStub()
        self._register_stub(CAPABILITIES_SERVICE_NAME, stub)

class CustomTestCase(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        self.app = buscall.app.test_client()
        self.custom_urlfetch_root = kwargs.get("root", URLFETCH_ROOT)
        super(CustomTestCase, self).__init__(*args, **kwargs)

    def setUp(self):
        self.testbed = CustomTestbed()
        self.testbed.activate()
        self.testbed.init_datastore_v3_stub()
        self.testbed.init_memcache_stub()
        self.testbed.init_custom_urlfetch_stub(enable=True, root=self.custom_urlfetch_root)
        self.testbed.init_mail_stub()
        self.testbed.init_user_stub()
        self.testbed.init_taskqueue_stub()
        self.testbed.init_capability_stub()

        # needed for task queue tests
        os.environ['HTTP_HOST'] = "localhost"

        # make sure we start out logged out
        self.logout()

    def tearDown(self):
        self.testbed.deactivate()

    def build_bus_entities(self, agency_id, route_id=None, direction_id=None, stop_id=None):
        if agency_id:
            agency_key = Key(Agency, agency_id)
        else:
            agency_key = None
        if route_id:
            route_key = Key(Route, "{0}|{1}".format(agency_id, route_id))
        else:
            route_key = None
        if direction_id:
            direction_key = Key(Direction, "{0}|{1}|{2}".format(agency_id, route_id, direction_id))
        else:
            direction_key = None
        if stop_id:
            stop_key = Key(Stop, "{0}|{1}|{2}|{3}".format(agency_id, route_id, direction_id, stop_id))
        else:
            stop_key = None

        groups = (
            (agency_key, Agency, route_key, "route_keys"),
            (route_key, Route, direction_key, "direction_keys"),
            (direction_key, Direction, stop_key, "stop_keys"),
            (stop_key, Stop, None, None),
        )
        for obj_key, obj_cls, subkey, subkeys_attr in groups:
            if not obj_key:
                continue
            obj = obj_key.get()
            if obj:
                if subkey and subkeys_attr:
                    subkeys = getattr(obj, subkeys_attr, [])
                    if subkey not in subkeys:
                        subkeys.append(subkey)
                        setattr(obj, subkeys_attr, subkeys)
                        obj.put()
            else:
                obj_id = obj_key.id().split("|")[-1]
                kwargs = {
                    "key": obj_key,
                    "name": obj_id,
                }
                if subkeys_attr:
                    if subkey:
                        kwargs[subkeys_attr] = [subkey]
                    else:
                        kwargs[subkeys_attr] = []
                obj = obj_cls(**kwargs)
                obj.put()

        # return keys that are not None
        keys = [agency_key, route_key, direction_key, stop_key]
        return [k for k in keys if k is not None]

    def build_entities_from_urlfetch_files(self, agencies=False,
            routes=False, directions=False, stops=False):
        """
        A reminder if the possible values you can pass for each argument:

        * True means load all the entities we can find for that entity type, given
          the parents we have. Passing routes=True means load all routes for
          this agency. Passing passing directions=True with routes="70" means
          load all directions within the 70 bus route only.
        * a string, or a list of strings, means only load the entities with the
          given id or ids. Passing routes="70" means only load the 70 bus route.
          Passing routes=["70", "556"] means only load the 70 bus and the 556
          bus routes.
        * an integer means to load up to that many entities, and no more, per parent.
          Precisely which entities get loaded is undefined. If the parent defines
          fewer entities than the integer specified, all of them are loaded.
          For example, if we pass routes=["70", "556"], directions=2, and the 70 bus
          defines 5 directions while the 556 bus defines 1, then 2 directions for
          the 70 bus will be loaded, and the single direction on the 556 bus will
          also be loaded. Note that passing 0 is functionally identical to passing
          False.
        * False means to not load any entities of the given type. This halts processing:
          if you define routes=False, then no directions or stops will be loaded,
          regardless of what arguments you specify for them.

        For this function, since it's only used for unit testing, all arguments
        default to False.
        """
        if not agencies:
            return

        # Late import so that we don't pull this function unless we need to.
        # Importing from buscall pulls a whole bunch of other imports, so
        # if we don't need to set up a lot of nextbus entities, we won't call
        # this build_entities_from_urlfetch_files function and do all that work.
        from buscall.views.tasks import load_nextbus_entities_for_agency

        # turn strings into a list of one entry
        if isinstance(agencies, basestring):
            agencies = [agencies]
        if isinstance(routes, basestring):
            routes = [routes]
        if isinstance(directions, basestring):
            directions = [directions]
        if isinstance(stops, basestring):
            stops = [stops]

        # get a list of actual agency ids
        if isinstance(agencies, (list, tuple)):
            agency_ids = agencies
        else:
            NEXTBUS_ROOT = os.path.join(URLFETCH_ROOT, "nextbus_api")
            agency_ids = [d for d in os.listdir(NEXTBUS_ROOT)
                    if os.path.isdir(os.path.join(NEXTBUS_ROOT, d))]
            if isinstance(agencies, int) and len(agency_ids) > agencies:
                agency_ids = agency_ids[0:agencies]

        # call our imported function
        for agency_id in agency_ids:
            load_nextbus_entities_for_agency(agency_id=agency_id, routes=routes,
                    directions=directions, stops=stops)

    def login(self, email, admin=False, user_id=None, create_user=True):
        if user_id:
            user_id = int(user_id)
        else:
            user_id = abs(hash(email))
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = str(user_id)
        os.environ['USER_IS_ADMIN'] = str(int(bool(admin))) # must be "0" or "1"
        if create_user:
            user_key = Key(User, user_id)
            user = user_key.get()
            if not user:
                user = User(key=user_key, primary_email = email)
                user.put()
            return user

    def logout(self):
        for key in ['USER_EMAIL', 'USER_ID', 'USER_IS_ADMIN']:
            if key in os.environ:
                del os.environ[key]

    @property
    def urlfetch_history(self):
        return self.testbed.get_stub(testbed.URLFETCH_SERVICE_NAME).history

    @property
    def urlfetch_responses(self):
        return self.testbed.get_stub(testbed.URLFETCH_SERVICE_NAME).responses
