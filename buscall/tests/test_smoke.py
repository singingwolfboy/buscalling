"Where there's smoke, there's fire."
import unittest
from buscall.tests.util import CustomTestCase
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
        assert rv.status.startswith("200"), rv.status
        agency = json.loads(rv.data)
        self.assertEqual(agency['id'], "mbta")
        assert isinstance(agency['route_ids'], list)
        rv2 = self.app.get('/agencies/mbta', headers={"Accept": "application/json"})
        self.assertEqual(rv.data, rv2.data)

    def test_api_routes(self):
        rv = self.app.get('/agencies/mbta/routes?format=json')
        assert rv.status.startswith("200"), rv.status
        routes = json.loads(rv.data)
        assert isinstance(routes, list)

