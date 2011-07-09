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
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER, parse_url_params

class TestException(Exception): pass

class FakeSocket(StringIO):
    def makefile(self, *args, **kw):
        return self

def httpparse(fp):
    socket = FakeSocket(fp.read())
    response = HTTPResponse(socket)
    response.begin()
    return response

class ServiceTestCase(unittest.TestCase):
  ''' 
  defines a test case, with appengine test stubs setup.
  Has methods to access email messages sent during the tested methods executed
  
  This class assists in creating AAA tests for appengine.
  Arrange, act and assert.
  Where the arrange step isn't duplicated between tests.

  '''
  class UrlFetchStub(urlfetch_stub.URLFetchServiceStub):
    """Stub version of the urlfetch API to be used with apiproxy_stub_map."""
    
    def _RetrieveURL(self, url, payload, method, headers, request, response,
                   follow_redirects=True, deadline=_API_CALL_DEADLINE,
                   validate_certificate=_API_CALL_VALIDATE_CERTIFICATE_DEFAULT):
      parts = urlparse(url)
      params = parse_url_params(parts.query)
      resp_file = None
      if parts.netloc == "webservices.nextbus.com":
        try:
          command = params['command']
        except KeyError:
          resp_file = os.path.join("urlfetch", "nextbus_api", "no_params.xml")
          break
        if command == "routeList":
          resp_file = os.path.join("urlfetch", "nextbus_api", params['a'], "route_list.xml")
        elif command == "routeConfig":
          resp_file = os.path.join("urlfetch", "nextbus_api", params['a'], params['r'], "config.xml")
        elif command == "predictions":
          resp_file = os.path.join("urlfetch", "nextbus_api", params['a'], params['r'], params['s']+".xml")
        else:
          raise TestException("unknown command: "+command)
      
      if not resp_file:
        raise TestException("unknown URL: "+url)

      with open(resp_file) as f:
        resp = httpparse(f)
        response.set_statuscode(resp.status)
        response.set_content(resp.fp.read())

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
    data = datafixture.data(datasets.BusListenerData, datasets.BusAlertData)
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
