# Utility functions and variables
from flask import request
import decimal
from google.appengine.ext import db
from google.appengine.ext.db import GqlQuery as TruthyGqlQuery
class GqlQuery(TruthyGqlQuery):
    def __nonzero__(self):
        return self.count(1) != 0

DAYS_OF_WEEK = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']
MAIL_SENDER = "Bus Calling <noreply@buscalling.appspotmail.com>"
DOMAIN = "http://www.buscalling.com"
READONLY_ERR_MSG = """
    Our database is currently in read-only mode. You can poke around and 
    explore the website, but nothing you do will be saved. Sorry about this:
    We'll be back to normal soon!
"""

def decimalproperty_factory(precision=2):
    """
    Returns a DecimalProperty class that stores decimals using 
    fixed-point arithmetic, for a given precision.
    """
    class DecimalProperty(db.Property):
        data_type = decimal.Decimal
        prec = precision

        def get_value_for_datastore(self, model_instance):
            d = super(DecimalProperty, self).get_value_for_datastore(model_instance)
            value = int(d._int)
            # if we were passed a decimal with smaller precision, bump it up
            # to the level we want.
            # Don't forget that d._exp is negative: 1.23 => 123 * 10**-2
            value = value * 10**(self.prec - abs(d._exp))
            return value

        def make_value_from_datastore(self, value):
            s = str(value)
            decimal_str = "%s.%s" % (s[0:self.prec], s[self.prec:])
            return decimal.Decimal(decimal_str)

        def validate(self, value):
            value = super(DecimalProperty, self).validate(value)
            if value is None:
                return value
            if isinstance(value, basestring):
                value = decimal.Decimal(value)
            if not isinstance(value, decimal.Decimal):
                raise db.BadValueError("Property %s must be a Decimal or string." % self.name)
            if abs(value._exp) > self.prec:
                raise db.BadValueError("Property %s can save at most %d digits of precision" % (self.name, self.prec))
            return value
    
    return DecimalProperty

CurrencyProperty = decimalproperty_factory(2)

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
    mimetype = mimetype.lower()
    if not mimetype:
        return 'html' # default
    choices = {
        'application/json': 'json',
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
