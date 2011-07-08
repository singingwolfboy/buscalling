#!/opt/local/bin/python2.5
from __future__ import with_statement 
import unittest
from gae_mock import ServiceTestCase
from urlfetch_mock import MockUrlfetchTestCase
from buscall import app
from buscall.models import nextbus
from buscall.models.listener import BusListener
from buscall.views.tasks import poll, reset_seen_flags
from buscall.util import APP_ID, AUTH_DOMAIN, LOGGED_IN_USER
from google.appengine.ext import db
import datetime

class UrlfetchTestCase(MockUrlfetchTestCase):
    # Mock responses to URLs are set in the setUp() method of the MockUrlfetchTestCase class

    def test_predictions(self):
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
        predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
        self.assertEqual(predictions.direction.title, "Ashmont Belt via Washington St.")
        self.assertEqual(len(predictions.buses), 3)
    
    def test_cron_no_listeners(self):
        quiet_moment = datetime.datetime(2011, 7, 2, 0, 0, 0) # Midnight on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(quiet_moment.timetuple())
            self.assertEqual(len(self.sent_messages), 0)
    
    def test_cron_with_listeners(self):
        active_moment = datetime.datetime(2011, 7, 2, 15, 10, 24) # 3:10:24 on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(active_moment.timetuple())
            self.assertEqual(len(self.sent_messages), 1)

class DatastoreTestCase(MockUrlfetchTestCase):
    def test_set_seen_flag(self):
        # get a listener that has alerts
        listeners = BusListener.gql("WHERE seen = False").fetch(5)
        listener = None
        for l in listeners:
            if l.alerts.count() > 0:
                listener = l
                break
        if not listener:
            raise Exception("Couldn't find a BusListener that has associated BusAlerts")

        for alert in listener.alerts:
            alert.execute()
        # refresh from db
        listener = BusListener.get(listener.key())
        self.assertTrue(listener.seen)

    def test_reset_seen_flags(self):
        seen = BusListener.gql("WHERE seen = True").fetch(1)
        self.assertTrue(len(seen) > 0)
        with app.test_request_context('/tasks/reset_seen_flags'):
            reset_seen_flags()
        seen = BusListener.gql("WHERE seen = True").fetch(1)
        self.assertEqual(len(seen), 0)

if __name__ == '__main__':
    unittest.main()
