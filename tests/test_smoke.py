"Where there's smoke, there's fire."
from tests.util import CustomTestCase
import simplejson as json

class SmokeTestCase(CustomTestCase):
    def test_homepage(self):
        self.logout()
        rv = self.app.get('/')
        assert rv.status.startswith("200"), rv.status

    def test_dashboard(self):
        self.login("test@example.com")
        rv = self.app.get('/', follow_redirects=True)
        assert rv.status.startswith("200"), rv.status

    def test_add_listener_form(self):
        self.logout()
        rv = self.app.get('/listeners/new')
        assert rv.status.startswith("303"), rv.status
        self.login("test@example.com")
        rv = self.app.get('/listeners/new')
        assert rv.status.startswith("200"), rv.status

    def test_api_agency(self):
        rv = self.app.get('/agencies/mbta?format=json')
        # before its loaded into the datastore, should get a 404
        assert rv.status.startswith("404"), rv.status
        # load it in, get 200
        # assert rv.status.startswith("200"), rv.status
        # agency = json.loads(rv.data)
        # self.assertEqual(agency['id'], "mbta")
        # assert isinstance(agency['routes'], dict)
        # rv2 = self.app.get('/agencies/mbta', headers={"Accept": "application/json"})
        # self.assertEqual(rv.data, rv2.data)

    def test_api_routes(self):
        rv = self.app.get('/agencies/mbta/routes?format=json')
        # before it's loaded into the datastore, should get a 404
        assert rv.status.startswith("404"), rv.status
        # load it in, test that it works
        # assert rv.status.startswith("200"), rv.status
        # routes = json.loads(rv.data)
        # assert isinstance(routes, list)

