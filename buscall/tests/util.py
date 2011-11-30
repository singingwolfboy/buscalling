from custom_testbed import CustomTestCase as CTC
import buscall
from fixture import GoogleDatastoreFixture, NamedDataStyle
import os

URLFETCH_ROOT = os.path.join(os.path.dirname(__file__), "urlfetch")
class CustomTestCase(CTC):
    def __init__(self, *args, **kwargs):
        self.app = buscall.app.test_client()
        self.fixture = GoogleDatastoreFixture(env=buscall.models, style=NamedDataStyle())
        root = kwargs.get("root", URLFETCH_ROOT)
        super(CustomTestCase, self).__init__(custom_urlfetch_root = root, *args, **kwargs)
