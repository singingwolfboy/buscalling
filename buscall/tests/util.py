from __future__ import with_statement
import os
import time
import unittest
import simplejson_mod as json
from httplib import HTTPResponse
from StringIO import StringIO
from urlparse import urlparse
from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api import mail_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api import user_service_stub
from google.appengine.api.memcache import memcache_stub
from google.appengine.api.urlfetch_stub import URLFetchServiceStub, \
  _API_CALL_DEADLINE, _API_CALL_VALIDATE_CERTIFICATE_DEFAULT
from fixture import GoogleDatastoreFixture, DataTestCase
from fixture.style import NamedDataStyle
import buscall
from buscall import models
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER
try:
  from urlparse import parse_qs
except ImportError:
  from cgi import parse_qs

class TestException(Exception): pass

# need to set AUTH_DOMAIN before we can create User objects,
# so just do this on import
if not 'AUTH_DOMAIN' in os.environ:
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN

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

class UrlFetchStub(urlfetch_stub.URLFetchServiceStub):

    def __init__(self, *args, **kwargs):
        super(UrlFetchStub, self).__init__(*args, **kwargs)
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
            return os.path.join("urlfetch", "nextbus_api", "no_params.xml")
        if command == "routeList":
            return os.path.join("urlfetch", "nextbus_api", params['a'][0], "route_list.xml")
        elif command == "routeConfig":
            return os.path.join("urlfetch", "nextbus_api", params['a'][0], params['r'][0], "config.xml")
        elif command == "predictions":
            return os.path.join("urlfetch", "nextbus_api", params['a'][0], params['r'][0], params['s'][0]+".xml")
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
          raise TestException("unknown URL: "+url)

        http_resp = httpparse(resp)
        content = http_resp.fp.read()
        response.set_statuscode(http_resp.status)
        response.set_content(content)
        self.history.append(url)
        self.responses[url] = content


class ServiceTestCase(unittest.TestCase):
    app = buscall.app.test_client()
    fixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())
    
    def setUp(self):
        # Ensure we're in UTC.
        os.environ['TZ'] = 'UTC'
        os.environ['SERVER_PORT'] = "8080"
        os.environ['SERVER_NAME'] = "localhost"
        os.environ['APPLICATION_ID'] = APP_ID

        self.urlfetch_stub = UrlFetchStub()
        self.mail_stub = mail_stub.MailServiceStub()
        self.memcache_stub = memcache_stub.MemcacheServiceStub()
        self.user_stub = user_service_stub.UserServiceStub()
        self.datastore_v3_stub = datastore_file_stub.DatastoreFileStub(APP_ID, None)

        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
        for stub_name in ('urlfetch', 'mail', 'memcache', 'user', 'datastore_v3'):
            apiproxy_stub_map.apiproxy.RegisterStub(stub_name, getattr(self, stub_name+"_stub"))
        
        # make sure we start out logged out
        self.logout()
        
        # do some black magic to detect if we're also subclassing from fixture.DataTestCase
        if DataTestCase in self.__class__.__mro__:
            DataTestCase.setUp(self)
  
    def login(self, email, admin=False, user_id=None):
        os.environ['USER_EMAIL'] = email
        os.environ['USER_ID'] = str(user_id) or str(abs(hash(email)))
        if admin:
          os.environ['USER_IS_ADMIN'] = "1"
        else:
          os.environ['USER_IS_ADMIN'] = "0"
  
    def logout(self):
        for key in ['USER_EMAIL', 'USER_ID', 'USER_IS_ADMIN']:
            if key in os.environ:
                del os.environ[key]
  
    def get_sent_messages(self, *args, **kwargs):
        return self.mail_stub.get_sent_messages(*args, **kwargs)
  
    @property
    def sent_messages(self):
        return self.get_sent_messages()
  
    @property
    def urlfetch_history(self):
        return self.urlfetch_stub.history
  
    @property
    def urlfetch_responses(self):
        return self.urlfetch_stub.responses
