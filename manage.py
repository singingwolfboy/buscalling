#!/opt/local/bin/python2.5
from __future__ import absolute_import
import sys
from main import get_updated_sys_path
sys.path = get_updated_sys_path()

# set up appengine modules: http://groups.google.com/group/google-appengine/browse_thread/thread/7c7cd1babc4484d
from google.appengine.api import urlfetch_stub
from google.appengine.api import apiproxy_stub_map 
from google.appengine.api import datastore_file_stub 
from google.appengine.api import mail_stub 
#from google3.apphosting.api import user_service_stub 
apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap() 
apiproxy_stub_map.apiproxy.RegisterStub('urlfetch', urlfetch_stub.URLFetchServiceStub()) 
#apiproxy_stub_map.apiproxy.RegisterStub('user', user_service_stub.UserServiceStub()) 
apiproxy_stub_map.apiproxy.RegisterStub('datastore_v3', datastore_file_stub.DatastoreFileStub('your_app_id', '/dev/null', '/dev/null')) 
apiproxy_stub_map.apiproxy.RegisterStub('mail', mail_stub.MailServiceStub())

from flaskext.script import Shell, Manager

from buscall import app
from buscall import models, views, forms
from google.appengine.ext import db

from credentials import SECRET_KEY
app.secret_key = SECRET_KEY

def _make_context():
    return {
        "app": app,
        "models": models,
        "views": views,
        "forms": forms,
        "db": db,
    }

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()
