#!/opt/local/bin/python2.5

# flush old data
import os
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