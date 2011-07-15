'''
Created on 16 apr 2010

@author: Morten Nielsen

You may change this code as you see fit, but you are expected to provide a
reference back to the original author, Morten Nielsen.

http://www.morkeleb.com/2010/06/28/testing-on-google-appengine-python-sdk/
'''
from __future__ import with_statement
import os
import time
import unittest
import simplejson as json
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
from fixture import GoogleDatastoreFixture
from fixture.style import NamedDataStyle
from buscall import models
from buscall.tests import datasets
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER
try:
  from urlparse import parse_qs
except ImportError:
  from cgi import parse_qs

class TestException(Exception): pass

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

class ServiceTestCase(unittest.TestCase):
  ''' 
  Defines a test case, with appengine test stubs setup.
  Has methods to access email messages sent during the tested methods executed
  
  This class assists in creating AAA tests for appengine.
  Arrange, act and assert.
  Where the arrange step isn't duplicated between tests.

  '''
  class UrlFetchStub(urlfetch_stub.URLFetchServiceStub):
    """Stub version of the urlfetch API to be used with apiproxy_stub_map."""

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
      response.set_statuscode(http_resp.status)
      response.set_content(http_resp.fp.read())

  def setUp(self):
    # Ensure we're in UTC.
    os.environ['TZ'] = 'UTC'
    os.environ['SERVER_PORT'] = "8080"
    os.environ['SERVER_NAME'] = "localhost"
    os.environ['APPLICATION_ID'] = APP_ID
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
    os.environ['USER_EMAIL'] = LOGGED_IN_USER

    self.urlfetch_stub = ServiceTestCase.UrlFetchStub()
    self.mail_stub = mail_stub.MailServiceStub()
    self.memcache_stub = memcache_stub.MemcacheServiceStub()
    self.user_stub = user_service_stub.UserServiceStub()
    self.datastore_v3_stub = datastore_file_stub.DatastoreFileStub(APP_ID, None)

    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    for stub_name in ('urlfetch', 'mail', 'memcache', 'user', 'datastore_v3'):
      apiproxy_stub_map.apiproxy.RegisterStub(stub_name, getattr(self, stub_name+"_stub"))
    
    # insert fixture data
    datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())
    data = datafixture.data(datasets.UserProfileData, datasets.BusListenerData, datasets.BusAlertData)
    data.setup()
  
  def get_sent_messages(self, *args, **kwargs):
    return self.mail_stub.get_sent_messages(*args, **kwargs)
  
  @property
  def sent_messages(self):
    return self.get_sent_messages()
  
  def get_urlfetch_responses(self):
    return self.urlfetch_stub.responses
  def set_urlfetch_responses(self, responses):
    self.urlfetch_stub.responses = responses
  urlfetch_responses = property(get_urlfetch_responses, set_urlfetch_responses)
  
  def update_urlfetch_responses(self, responses):
    self.urlfetch_stub.responses.update(responses)

  def set_urlfetch_response(self, url, content):
    "sets the content that will be returned for a given url when fetched"
    self.urlfetch_stub.set_content(url, content)
  
  def update_responses(self, responses):
    ""
    self.urlfetch_stub.responses = responses
