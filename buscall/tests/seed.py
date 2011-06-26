#!/opt/local/bin/python2.5
from __future__ import absolute_import
from os import path
import sys
root_path = path.dirname(path.dirname(path.dirname(path.abspath(__file__))))
lib_path = path.join(root_path, 'lib')
sys.path.insert(0, lib_path)
sys.path.insert(0, root_path)

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