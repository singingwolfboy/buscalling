from buscall.tests.util import CustomTestCase
import simplejson as json

class APITestCase(CustomTestCase):
    def test_limit(self):
        rv = self.app.get('/agencies/mbta/routes?format=json')
        routes = json.loads(rv.data)
        assert len(routes) <= 20

