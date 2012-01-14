from __future__ import with_statement
import unittest
from ndb import Key
import datetime
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.nextbus import Agency, Route, Direction, Stop
from buscall.models.listener import BusListener
from buscall.models.user import User
from tests.util import CustomTestCase

class BusListenerTestCase(CustomTestCase):
    def test_create_recurring_bus_listener(self):
        num_listeners = BusListener.query().count()
        user_key = Key(User, "carl@example.com")
        listener = BusListener(
            user_key=user_key,
            agency_key=Key(Agency, "mbta"),
            route_key=Key(Route, "mbta|556"),
            direction_key=Key(Direction, "mbta|556|556_1_var0"),
            stop_key=Key(Stop, "mbta|556|556_1_var0|77378"),
            start=datetime.time(3,0),
            recur=True, mon=True, tue=False, wed=True, thu=True, fri=True, sat=False, sun=False)
        listener.put()
        self.assertEqual(BusListener.query().count() - num_listeners, 1)
        self.assertTrue(listener.recur)
        self.assertEqual(listener.user_key, user_key)
        self.assertEqual(listener.start, datetime.time(3,0))
        # with app.test_request_context('/poll'):
        #     self.assertEqual(listener.agency.id, "mbta")
        #     self.assertEqual(listener.route.id, "556")
        #     self.assertEqual(listener.stop.id, "77378")
    
    def test_create_one_time_bus_listener(self):
        num_listeners = BusListener.query().count()
        user_key = Key(User, "carl@example.com")
        listener = BusListener(user_key=user_key,
            agency_key=Key(Agency, "mbta"),
            route_key=Key(Route, "mbta|556"),
            direction_key=Key(Direction, "mbta|556|556_1_var0"),
            stop_key=Key(Stop, "mbta|556|556_1_var0|77378"),
            start=datetime.time(3,0), recur=False, mon=True, tue=False, wed=True, thu=True, fri=True, sat=False, sun=False)
        listener.put()
        self.assertEqual(BusListener.query().count() - num_listeners, 1)
        self.assertFalse(listener.recur)
        self.assertEqual(listener.user_key, user_key)
        self.assertEqual(listener.start, datetime.time(3,0))
