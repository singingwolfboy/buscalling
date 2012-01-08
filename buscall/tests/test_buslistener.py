from __future__ import with_statement
import unittest
from ndb import Key
import datetime
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.nextbus import Agency, Route, Direction, Stop
from buscall.models.listener import BusListener
from buscall.models.profile import UserProfile
from buscall.tests.util import CustomTestCase
from google.appengine.api.users import User

class BusListenerTestCase(CustomTestCase):
    def test_create_recurring_bus_listener(self):
        num_listeners = BusListener.query().count()
        user = User("carl@example.com")
        profile_key = Key(UserProfile, user.user_id())
        listener = BusListener(
            profile_key=profile_key,
            agency_key=Key(Agency, "mbta"),
            route_key=Key(Route, "556"),
            direction_key=Key(Direction, "556_1_var0"),
            stop_key=Key(Stop, "77378"),
            start=datetime.time(3,0),
            recur=True, mon=True, tue=False, wed=True, thu=True, fri=True, sat=False, sun=False)
        listener.put()
        self.assertEqual(BusListener.query().count() - num_listeners, 1)
        self.assertTrue(listener.recur)
        self.assertEqual(listener.profile_key, profile_key)
        self.assertEqual(listener.seen, False)
        self.assertEqual(listener.start, datetime.time(3,0))
        with app.test_request_context('/poll'):
            self.assertEqual(listener.agency.id, "mbta")
            self.assertEqual(listener.route.id, "556")
            self.assertEqual(listener.stop.id, "77378")
    
    def test_create_one_time_bus_listener(self):
        num_listeners = BusListener.all().count()
        user = User("carl@example.com")
        profile = UserProfile.get_or_insert_by_user(user)
        listener = BusListener(userprofile=profile, agency_id="mbta", route_id="556", direction_id="556_1_var0", stop_id="77378",
            start=datetime.time(3,0), recur=False, mon=True, tue=False, wed=True, thu=True, fri=True, sat=False, sun=False)
        listener.put()
        self.assertEqual(BusListener.all().count() - num_listeners, 1)
        self.assertFalse(listener.recur)
        self.assertEqual(listener.userprofile, profile)
        self.assertEqual(listener.start, datetime.time(3,0))
