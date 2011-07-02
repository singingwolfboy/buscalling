# Utility functions and variables
from google.appengine.ext.db import GqlQuery as TruthyGqlQuery
class GqlQuery(TruthyGqlQuery):
    def __nonzero__(self):
        return self.count(1) != 0

DAYS_OF_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
MAIL_SENDER = "Bus Calling <noreply@buscalling.appspotmail.com>"

def url_params(params):
    try:
        # if we were passed a dictionary, convert it into a list of tuples
        params = params.items()
    except AttributeError:
        pass
    return "&".join(["%s=%s" % (key, val) for (key, val) in params])

def clean_booleans(d):
    for key in d.keys():
        try:
            val = d[key].lower()
            if val == 'true' or val == 't':
                d[key] = True
            elif val == 'false' or val == 'f':
                d[key] = False
        except AttributeError:
            pass
    return d

# for testing only
APP_ID = u'buscalling'
DATASTORE_FILE = '/tmp/appengine-datastore' # or /dev/null
AUTH_DOMAIN = 'gmail.com'
LOGGED_IN_USER = 'test@example.com' # set to '' for no logged in user 
LOGGED_IN_USER_ID = '123456'
LOGGED_IN_USER_ADMIN = '0' # set to '1' for admin user

def setup_for_testing():
    "Do all setup assuming that sys.path has already been fixed"
    import os
    os.environ['APPLICATION_ID'] = APP_ID
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
    os.environ['USER_EMAIL'] = LOGGED_IN_USER
    os.environ['USER_ID'] = LOGGED_IN_USER_ID
    os.environ['USER_IS_ADMIN'] = LOGGED_IN_USER_ADMIN

    # set up appengine modules: http://groups.google.com/group/google-appengine/browse_thread/thread/7c7cd1babc4484d
    from google.appengine.api import urlfetch_stub
    from google.appengine.api import apiproxy_stub_map 
    from google.appengine.api import datastore_file_stub 
    from google.appengine.api import mail_stub 
    from google.appengine.api import user_service_stub 
    apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap() 
    apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub()) 
    apiproxy_stub_map.apiproxy.RegisterStub('user', user_service_stub.UserServiceStub()) 
    apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', datastore_file_stub.DatastoreFileStub(APP_ID, DATASTORE_FILE)) 
    apiproxy_stub_map.apiproxy.RegisterStub('mail', mail_stub.MailServiceStub())

    from buscall import app
    from buscall.credentials import SECRET_KEY
    app.secret_key = SECRET_KEY