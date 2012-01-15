from tests.util import CustomTestCase
import simplejson as json

class APITestCase(CustomTestCase):
    def test_limit_agencies(self):
        self.build_entities_from_urlfetch_files(agencies=30)
        rv = self.app.get('/agencies?format=json')
        agencies = json.loads(rv.data)
        assert len(agencies) == 20
        rv = self.app.get('/agencies?format=json&limit=15')
        agencies = json.loads(rv.data)
        assert len(agencies) == 15

    def test_limit_routes(self):
        self.build_entities_from_urlfetch_files(agencies="mbta", routes=30)
        rv = self.app.get('/agencies/mbta/routes?format=json')
        routes = json.loads(rv.data)
        assert len(routes) == 20
        rv = self.app.get('/agencies/mbta/routes?format=json&limit=15')
        routes = json.loads(rv.data)
        assert len(routes) == 15

