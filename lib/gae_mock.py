'''
Created on 16 apr 2010

@author: Morten Nielsen

You may change this code as you see fit, but you are expected to provide a
reference back to the original author, Morten Nielsen.

http://www.morkeleb.com/2010/06/28/testing-on-google-appengine-python-sdk/
'''
import os
import time
import unittest
from httplib import HTTPResponse
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
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER, DATASTORE_FILE
TEST_DATASTORE_FILE = DATASTORE_FILE + "_test"

class ServiceTestCase(unittest.TestCase):
  ''' 
  defines a test case, with appengine test stubs setup.
  Has methods to access email messages sent during the tested methods executed
  
  This class assists in creating AAA tests for appengine.
  Arrange, act and assert.
  Where the arrange step isn't duplicated between tests.

  '''
  class LoggingMailStub(mail_stub.MailServiceStub):
    def __init__(self, host=None, port=25, user='', password='',
          enable_sendmail=False, show_mail_body=False, service_name='mail'):
      """Constructor.

      Args:
        host: Host of SMTP mail server.
        post: Port of SMTP mail server.
        user: Sending user of SMTP mail.
        password: SMTP password.
        enable_sendmail: Whether sendmail enabled or not.
        show_mail_body: Whether to show mail body in log.
        service_name: Service name expected for all calls.
      """
      super(mail_stub.MailServiceStub, self).__init__(service_name)
      self._smtp_host = host
      self._smtp_port = port
      self._smtp_user = user
      self._smtp_password = password
      self._enable_sendmail = enable_sendmail
      self._show_mail_body = show_mail_body
      self.messages = []

    def _GenerateLog(self, method, message, log):
      self.messages.append(message)
      return
    
  class Struct:
    def __init__(self, **entries): self.__dict__.update(entries)
    def __repr__(self):
        args = ['%s=%s' % (k, repr(v)) for (k, v) in vars(self).items()]
        return 'Struct(%s)' % ', '.join(args)

  class UrlFetchStub(urlfetch_stub.URLFetchServiceStub):
    """Stub version of the urlfetch API to be used with apiproxy_stub_map."""

    def __init__(self, service_name='urlfetch'):
      """Initializer.

      Args:
        service_name: Service name expected for all calls.
      """
      self.responses = {};
      super(URLFetchServiceStub, self).__init__(service_name)
    
    def _RetrieveURL(self, url, payload, method, headers, request, response,
                   follow_redirects=True, deadline=_API_CALL_DEADLINE,
                   validate_certificate=_API_CALL_VALIDATE_CERTIFICATE_DEFAULT):
      response.set_statuscode(200)
      response.set_content(self.responses[url])
      
    def set_content(self, url, c):
      self.responses[url] = c

  def setUp(self):
    # Ensure we're in UTC.
    os.environ['TZ'] = 'UTC'
    os.environ['SERVER_PORT'] = "8080"
    os.environ['SERVER_NAME'] = "localhost"
    os.environ['APPLICATION_ID'] = APP_ID
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
    os.environ['USER_EMAIL'] = LOGGED_IN_USER

    # flush old data
    if os.path.exists(TEST_DATASTORE_FILE):
      os.remove(TEST_DATASTORE_FILE)

    self.urlfetch_stub = ServiceTestCase.UrlFetchStub()
    self.mail_stub = ServiceTestCase.LoggingMailStub()
    self.memcache_stub = memcache_stub.MemcacheServiceStub()
    self.user_stub = user_service_stub.UserServiceStub()
    self.datastore_v3_stub = datastore_file_stub.DatastoreFileStub(APP_ID, TEST_DATASTORE_FILE)

    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()
    for stub_name in ('urlfetch', 'mail', 'memcache', 'user', 'datastore_v3'):
      apiproxy_stub_map.apiproxy.RegisterStub(stub_name, getattr(self, stub_name+"_stub"))
    
    # insert new data
    datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())
    data = datafixture.data(datasets.BusListenerData)
    data.setup()
  
  @property
  def mail_messages(self):
    return self.mail_stub.messages
  
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
