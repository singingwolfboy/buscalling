import os
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
from fixture import DataTestCase, GoogleDatastoreFixture, NamedDataStyle
import buscall
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
            return open(os.path.join(os.path.dirname(__file__), rel_path))
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
        self.fixture = GoogleDatastoreFixture(env=buscall.models, style=NamedDataStyle())
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
        self.testbed.init_capability_stub()

        # make sure we start out logged out
        self.logout()
        
        # do some black magic to detect if we're also subclassing from fixture.DataTestCase
        if DataTestCase in self.__class__.__mro__:
            DataTestCase.setUp(self)
    
    def tearDown(self):
        self.testbed.deactivate()
  
    def login(self, email, admin=False, user_id=None):
        os.environ['USER_EMAIL'] = email
        if user_id:
            os.environ['USER_ID'] = str(user_id)
        else:
            os.environ['USER_ID'] = str(abs(hash(email)))
        if admin:
          os.environ['USER_IS_ADMIN'] = "1"
        else:
          os.environ['USER_IS_ADMIN'] = "0"
  
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
