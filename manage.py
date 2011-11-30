#!/usr/bin/env python
import sys
import os
# add lib dir to path
libdir = os.path.join(os.path.dirname(__file__), 'lib')
sys.path.insert(0, libdir)

from custom_testbed import CustomTestbed
testbed = CustomTestbed()
testbed.activate()
testbed.init_datastore_v3_stub()
testbed.init_memcache_stub()
testbed.init_urlfetch_stub()
testbed.init_capability_stub()

from buscall import app
from buscall import models, views, forms
from google.appengine.ext import db
from flaskext.script import Shell, Manager

def _make_context():
    return {
        "app": app,
        "models": models,
        "views": views,
        "forms": forms,
        "db": db,
        "testbed": testbed,
    }

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))
manager.run()

testbed.deactivate()
