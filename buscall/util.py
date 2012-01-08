# Utility functions and variables
from flask import request
import decimal
from google.appengine.ext import db
from ndb import model

DAYS_OF_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
MAIL_SENDER = "Bus Calling <noreply@buscalling.appspotmail.com>"
DOMAIN = "http://www.buscalling.com"
READONLY_ERR_MSG = """
    Our database is currently in read-only mode. You can poke around and
    explore the website, but nothing you do will be saved. Sorry about this:
    We'll be back to normal soon!
"""

class DecimalModel(model.Model):
    int = model.IntegerProperty(required=True)
    exp = model.IntegerProperty(default=1)
    sign = model.BooleanProperty(default=True)

    def __init__(self, value, **kwargs):
        if isinstance(value, (basestring, int)):
            value = decimal.Decimal(value)
        if isinstance(value, decimal.Decimal):
            kwargs["int"] = int(value._int)
            kwargs["exp"] = int(value._exp)
            kwargs["sign"] = bool(value._sign)
        else:
            kwargs["key"] = value
        super(DecimalModel, self).__init__(**kwargs)

    def _to_decimal(self):
        d = decimal.Decimal()
        d._int = str(self.int)
        d._exp = self.exp
        d._sign = int(self.sign)
        return d

class DecimalProperty(model.StructuredProperty):
    def __init__(self, **kwds):
        super(DecimalProperty, self).__init__(DecimalModel, **kwds)

    def _validate(self, value):
        assert isinstance(value, decimal.Decimal)

    def _to_base_type(self, value):
        return DecimalModel(value)

    def _from_base_type(self, value):
        return value._to_decimal()


# based on http://flask.pocoo.org/snippets/45/
def get_request_format():
    """
    Returns the format that the user requests.
    Ideally, returns a short string like "html" or "json".
    If given an unknown mimetype like "Accepts: foo/bar", returns
    the text after the slash: in this example, "bar". If given
    something completely unknown, returns it. If given nothing,
    returns "html" as a default. All return values are lowercased.
    """
    # if the user specifies a `format` HTTP parameter, use that
    mimetype = request.args.get('format', '').strip() or \
        request.accept_mimetypes.best
    if not mimetype:
        return 'html' # default
    mimetype = mimetype.lower()
    choices = {
        'application/json': 'json',
        'text/javascript': 'json',
        'application/twiml': 'twiml',
        'text/html': 'html',
        'text/plain': 'text',
    }
    if mimetype in choices:
        return choices[mimetype]
    bits = mimetype.split("/")
    if len(bits) == 2:
        return bits[-1]
    return mimetype

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

def filter_keys(d, allowed):
    for key in d.keys():
        if key not in allowed:
            del d[key]
    return d

def pluralize_minutes(minutes):
    if minutes == 0:
        return "less than a minute"
    elif minutes == 1:
        return "one minute"
    else:
        return "%s minutes" % (minutes)

def humanize_list(lst):
    if not hasattr(lst, "__len__"):
        lst = list(lst)
    if len(lst) == 0:
        return ""
    elif len(lst) == 1:
        return lst[0]
    elif len(lst) == 2:
        return " and ".join(lst)
    else:
        return ", ".join(lst[:-1]) + ", and " + lst[-1]

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
