from __future__ import with_statement
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.listener import BusListener, BusNotification
from buscall.models.profile import UserProfile
from buscall.views.tasks import reset_seen_flags
from buscall.tests.util import ServiceTestCase

from fixture import DataSet, DataTestCase
import datetime
from google.appengine.api.users import User

class UserProfileData(DataSet):
    class test_profile:
        user = User("test@example.com")
        subscribed = True
        credits = 8
        joined = datetime.datetime(2010, 2, 3, 10, 32, 45)
        last_login = datetime.datetime(2011, 7, 14, 7, 0, 0)

    class with_phone:
        user = User("phone@example.com")
        subscribed = True
        credits = 0
        phone = "999-888-7777"
        joined = datetime.datetime(2011, 2, 9, 10, 11, 12)
        last_login = datetime.datetime(2011, 6, 10, 10, 15)

class BusListenerData(DataSet):
    class morning_bus:
        userprofile = UserProfileData.test_profile
        agency_id = "mbta"
        route_id = "556"
        direction_id = "556_5560006v0_1"
        stop_id = "77378"
        recur = True
        mon = True
        tue = True
        wed = True
        thu = True
        fri = True
        sat = False
        sun = False
        start = datetime.time(8, 0) # 8:00 AM
        seen = False

    class seen_bus:
        userprofile = UserProfileData.with_phone
        agency_id = "mbta"
        route_id = "70"
        direction_id = "70_0_var1"
        stop_id = "88333"
        recur = True
        mon = True
        tue = False
        wed = True
        thu = False
        fri = True
        sat = False
        sun = True
        start = datetime.time(4,0)
        seen = True

class BusNotificationData(DataSet):
    class morning_bus_20_min:
        listener = BusListenerData.morning_bus
        minutes = 20
        medium = "email"
        executed = False

    class seen_bus_email_notification:
        listener = BusListenerData.seen_bus
        minutes = 3
        medium = "email"
        executed = True

    class seen_bus_phone_notification:
        listener = BusListenerData.seen_bus
        minutes = 5
        medium = "phone"
        executed = False

class DatastoreTestCase(ServiceTestCase, DataTestCase):
    datasets = [UserProfileData, BusListenerData, BusNotificationData]

    def test_set_seen_flag(self):
        # get a listener that has notifications
        listener = BusListener.gql("WHERE seen = False").fetch(1)[0]
        assert not listener.seen
        for notification in listener.notifications:
            notification.execute()
        # refresh from db
        key = listener.key()
        del listener
        listener = BusListener.get(key)
        assert listener.seen

    def test_reset_seen_flags(self):
        seen = BusListener.gql("WHERE seen = True").fetch(1)
        assert len(seen) == 1
        self.assertTrue(len(seen) > 0)
        with app.test_request_context('/tasks/reset_seen_flags'):
            reset_seen_flags()
        seen = BusListener.gql("WHERE seen = True").fetch(1)
        self.assertEqual(len(seen), 0)
      