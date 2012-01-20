"Where there's smoke, there's fire."
from tests.util import CustomTestCase
import simplejson as json
from functools import partial

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

    def test_api_agencies(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before its loaded into the datastore, should get a 404
        rv = self.app.get('/agencies/mbta?format=json')
        assert rv.status.startswith("404"), rv.status
        # load it in, get 200
        self.build_entities_from_urlfetch_files(agencies="mbta")
        rv = self.app.get('/agencies/mbta?format=json')
        assert rv.status.startswith("200"), rv.status
        agency = json.loads(rv.data)
        self.assertEqual(agency['id'], "mbta")
        rv2 = get_json('/agencies/mbta')
        self.assertEqual(rv.data, rv2.data)

    def test_api_routes(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before it's loaded into the datastore, should get a 404
        rv = self.app.get('/agencies/mbta/routes?format=json')
        assert rv.status.startswith("404"), rv.status
        rv = self.app.get('/agencies/mbta/routes/70?format=json')
        assert rv.status.startswith("404"), rv.status

        # load it in, test that it works
        self.build_entities_from_urlfetch_files(agencies="mbta", routes=True)
        agency_resp = get_json('/agencies/mbta')
        agency = json.loads(agency_resp.data)
        self.assertIsInstance(agency['routes'], dict)

        rv = self.app.get('/agencies/mbta/routes?format=json')
        assert rv.status.startswith("200"), rv.status
        routes = json.loads(rv.data)
        self.assertIsInstance(routes, list)

        r70_resp = get_json('/agencies/mbta/routes/70')
        assert r70_resp.status.startswith("200"), r70_resp.status
        r70 = json.loads(r70_resp.data)
        self.assertIsInstance(r70, dict)
        self.assertEqual(r70['id'], "70")

    def test_api_directions(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before it's loaded into the datastore, should get a 404
        rv = self.app.get('/agencies/mbta/routes/70/directions?format=json')
        assert rv.status.startswith("404"), rv.status
        rv = self.app.get('/agencies/mbta/routes/70/directions/70_0_var0?format=json')
        assert rv.status.startswith("404"), rv.status

        # load it in
        self.build_entities_from_urlfetch_files(agencies="mbta", routes="70", directions=True)
        rv = get_json('/agencies/mbta/routes/70')
        assert rv.status.startswith("200"), rv.status
        route = json.loads(rv.data)
        self.assertIsInstance(route['directions'], dict)

        rv = self.app.get('agencies/mbta/routes/70/directions')
        assert rv.status.startswith("200"), rv.status

