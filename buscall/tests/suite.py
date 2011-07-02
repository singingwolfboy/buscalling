#!/opt/local/bin/python2.5
from __future__ import with_statement 
import unittest
from urlfetch_mock import MockUrlfetchTestCase
from buscall import app
from buscall.models import nextbus
from buscall.views.tasks import poll
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER
import datetime

class UrlfetchTestCase(MockUrlfetchTestCase):
    # Mock responses to URLs are set in the setUp() method of the MockUrlfetchTestCase class

    def test_predictions(self):
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
        predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
        self.assertEqual(predictions['direction'], "Ashmont Belt via Washington St.")
        self.assertEqual(len(predictions['buses']), 3)
    
    def test_cron_no_listeners(self):
        quiet_moment = datetime.datetime(2011, 6, 2, 0, 0, 0) # Midnight on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(quiet_moment.timetuple())
            self.assertEqual(len(self.mail_messages), 0)

if __name__ == '__main__':
    unittest.main()
