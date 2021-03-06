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
        rv = get_json('/agencies/mbta')
        assert rv.status.startswith("404"), rv.status

        # load it in, get 200
        self.build_entities_from_urlfetch_files(agencies="mbta")
        rv = get_json('/agencies/mbta')
        assert rv.status.startswith("200"), rv.status
        self.assertEqual(rv.data,
                self.app.get('/agencies/mbta?format=json').data)
        agency = json.loads(rv.data)
        self.assertEqual(agency['id'], "mbta")

    def test_api_routes(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before it's loaded into the datastore, should get a 404
        rv = get_json('/agencies/mbta/routes')
        assert rv.status.startswith("404"), rv.status
        rv = get_json('/agencies/mbta/routes/70')
        assert rv.status.startswith("404"), rv.status

        # load it in, test that it works
        self.build_entities_from_urlfetch_files(agencies="mbta", routes=True)
        agency_resp = get_json('/agencies/mbta')
        assert agency_resp.status.startswith("200"), agency_resp.status
        agency = json.loads(agency_resp.data)
        self.assertIsInstance(agency['routes'], dict)

        rv = get_json('/agencies/mbta/routes')
        assert rv.status.startswith("200"), rv.status
        self.assertEqual(rv.data,
                self.app.get('/agencies/mbta/routes?format=json').data)
        routes = json.loads(rv.data)
        self.assertIsInstance(routes, list)

        r70_resp = get_json('/agencies/mbta/routes/70')
        assert r70_resp.status.startswith("200"), r70_resp.status
        self.assertEqual(r70_resp.data,
                self.app.get('/agencies/mbta/routes/70?format=json').data)
        r70 = json.loads(r70_resp.data)
        self.assertIsInstance(r70, dict)
        self.assertEqual(r70['id'], "70")

    def test_api_directions(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before it's loaded into the datastore, should get a 404
        rv = get_json('/agencies/mbta/routes/70/directions')
        assert rv.status.startswith("404"), rv.status
        rv = get_json('/agencies/mbta/routes/70/directions/70_0_var0')
        assert rv.status.startswith("404"), rv.status

        # load it in
        self.build_entities_from_urlfetch_files(agencies="mbta", routes="70", directions=True)
        rv = get_json('/agencies/mbta/routes/70')
        assert rv.status.startswith("200"), rv.status
        self.assertEqual(rv.data,
                self.app.get('/agencies/mbta/routes/70?format=json').data)
        route = json.loads(rv.data)
        self.assertIsInstance(route['directions'], dict)

        rv = get_json('agencies/mbta/routes/70/directions')
        assert rv.status.startswith("200"), rv.status
        self.assertEqual(rv.data,
                self.app.get('agencies/mbta/routes/70/directions?format=json').data)
        directions = json.loads(rv.data)
        self.assertIsInstance(directions, list)

        direction_resp = get_json('/agencies/mbta/routes/70/directions/70_0_var0')
        assert direction_resp.status.startswith("200"), direction_resp.status
        self.assertEqual(direction_resp.data,
                self.app.get('/agencies/mbta/routes/70/directions/70_0_var0?format=json').data)
        direction = json.loads(direction_resp.data)
        self.assertIsInstance(direction, dict)
        self.assertEqual(direction['id'], "70_0_var0")

    def test_api_stops(self):
        get_json = partial(self.app.get, headers={"Accept": "application/json"})

        # before it's loaded into the datastore, should get a 404
        rv = get_json('/agencies/mbta/routes/70/directions/70_0_var0/stops')
        assert rv.status.startswith("404"), rv.status
        rv = get_json('/agencies/mbta/routes/70/directions/70_0_var0/stops/8820')
        assert rv.status.startswith("404"), rv.status

        # load it in
        self.build_entities_from_urlfetch_files(agencies="mbta", routes="70", directions="70_0_var0", stops=True)

        rv = get_json('agencies/mbta/routes/70/directions/70_0_var0/stops')
        assert rv.status.startswith("200"), rv.status
        self.assertEqual(rv.data,
                self.app.get('agencies/mbta/routes/70/directions/70_0_var0/stops?format=json').data)
        stops = json.loads(rv.data)
        self.assertIsInstance(stops, list)

        stop_resp = get_json('/agencies/mbta/routes/70/directions/70_0_var0/stops/8820')
        assert stop_resp.status.startswith("200"), stop_resp.status
        self.assertEqual(stop_resp.data,
                self.app.get('/agencies/mbta/routes/70/directions/70_0_var0/stops/8820?format=json').data)
        stop = json.loads(stop_resp.data)
        self.assertIsInstance(stop, dict)
        self.assertEqual(stop['id'], "8820")
