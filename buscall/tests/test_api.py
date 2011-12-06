from buscall.tests.util import CustomTestCase
import simplejson as json
from buscall import app
from flask import g

class APITestCase(CustomTestCase):
    def test_limit_internal(self):
        with app.test_request_context('/agencies?format=json'):
            app.preprocess_request()
            assert g.limit == 20
        with app.test_request_context('/agencies?format=json&limit=15'):
            app.preprocess_request()
            assert g.limit == 15

    def test_limit_agencies(self):
        rv = self.app.get('/agencies?format=json')
        agencies = json.loads(rv.data)
        assert len(agencies) == 20
        rv = self.app.get('/agencies?format=json&limit=15')
        agencies = json.loads(rv.data)
        assert len(agencies) == 15

    def test_limit_routes(self):
        rv = self.app.get('/agencies/mbta/routes?format=json')
        routes = json.loads(rv.data)
        assert len(routes) == 20
        rv = self.app.get('/agencies/mbta/routes?format=json&limit=15')
        routes = json.loads(rv.data)
        assert len(routes) == 15

