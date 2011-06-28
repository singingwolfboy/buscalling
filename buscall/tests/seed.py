#!/opt/local/bin/python2.5
from __future__ import absolute_import
import os
import sys
dirname = os.path.dirname
root_path = dirname(dirname(dirname(os.path.abspath(__file__))))
lib_path = os.path.join(root_path, 'lib')
sys.path.insert(0, lib_path)
sys.path.insert(0, root_path)

# flush old data
from buscall.util import DATASTORE_FILE
if os.path.exists(DATASTORE_FILE):
    os.remove(DATASTORE_FILE)

from buscall.util import setup_for_testing
setup_for_testing()

from buscall import models
from buscall.tests import datasets
from fixture import GoogleDatastoreFixture
from fixture.style import NamedDataStyle

datafixture = GoogleDatastoreFixture(env=models, style=NamedDataStyle())
data = datafixture.data(datasets.BusListenerData)
data.setup()
print "Data loaded into datastore"