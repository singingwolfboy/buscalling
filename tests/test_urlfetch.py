import datetime
from ndb import Key
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction
from buscall.models.profile import UserProfile
from buscall.models.listener import ScheduledNotification
from buscall.views.tasks import poll
from buscall.credentials import ACCOUNT_SID
from buscall.tests.util import CustomTestCase
from google.appengine.ext import testbed

from fixture import DataSet, DataTestCase

class UserProfileData(DataSet):
    class test_profile:
        user_id = "test@example.com"
        subscribed = True
        credits = 8
        joined = datetime.datetime(2010, 2, 3, 10, 32, 45)
        last_access = datetime.datetime(2011, 7, 14, 7, 0, 0)

    class with_phone:
        user_id = "phone@example.com"
        subscribed = True
        credits = 0
        phone = "999-888-7777"
        joined = datetime.datetime(2011, 2, 9, 10, 11, 12)
        last_access = datetime.datetime(2011, 6, 10, 10, 15)

class ScheduledNotificationData(DataSet):
    class cron_bus_20_min:
        minutes_before = 20
        medium = "email"
        has_executed = False

    class seen_bus_phone_notification:
        minutes_before = 5
        medium = "phone"
        has_executed = False

cron_bus_notification = ScheduledNotification(
        minutes_before=20, medium="email", has_executed=False)
seen_bus_notification = ScheduledNotification(
        minutes_before=5, medium="phone", has_executed=False)

class BusListenerData(DataSet):
    class cron_bus:
        profile_key = Key(UserProfile, "test@example.com")
        agency_key = Key(Agency, "mbta")
        route_key = Key(Route, "26")
        direction_key = Key(Direction, "26_1_var1")
        stop_key = Key(Stop, "492")
        recur = True
        mon = False
        tue = False
        wed = False
        thu = False
        fri = False
        sat = True
        sun = True
        start = datetime.time(15,00) # 3:00 PM
        scheduled_notifications = [cron_bus_notification]

    class seen_bus:
        userprofile = UserProfileData.with_phone
        agency_id = "mbta"
        route_id = "70"
        direction_id = "70_1_var0"
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
        scheduled_notifications = [seen_bus_notification]

class UrlfetchTestCase(CustomTestCase, DataTestCase):
    datasets = [UserProfileData, BusListenerData] #  , ScheduledNotificationData]

    def test_predictions(self):
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
        predictions = BusPrediction.query(agency_id=agency_id, route_id=route_id,
                direction_id=direction_id, stop_id=stop_id)
        self.assertEqual(len(predictions), 3)
    
    def test_cron_no_listeners(self):
        mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        quiet_moment = datetime.datetime(2011, 7, 2, 0, 0, 0) # Midnight on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(quiet_moment.timetuple())
            messages = mail_stub.get_sent_messages()
            self.assertEqual(len(messages), 0)
    
    def test_cron_with_listeners(self):
        mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        active_moment = datetime.datetime(2011, 7, 2, 15, 10, 24) # 3:10:24 on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(active_moment.timetuple())
            messages = mail_stub.get_sent_messages()
            self.assertEqual(len(messages), 1)
    
    def test_call_prediction(self):
        self.login("bill@gmail.com", admin=True)
        self.app.get('/call/mbta/26/26_1_var1/492/9999999999')
        url = "https://api.twilio.com/2010-04-01/Accounts/%s/Calls.json" % (ACCOUNT_SID,)
        self.assertTrue(url in self.urlfetch_history)

    def test_sms_prediction(self):
        self.login("bill@gmail.com", admin=True)
        self.app.get('/sms/mbta/26/26_1_var1/492/9999999999')
        url = "https://api.twilio.com/2010-04-01/Accounts/%s/SMS/Messages.json" % (ACCOUNT_SID,)
        assert url in self.urlfetch_history

    def test_phone_notification(self):
        notification = ScheduledNotification.query(
                ScheduledNotification.medium == "phone",
                ScheduledNotification.has_executed == False)[0]
        with app.test_request_context('/tasks/poll'):
            result = twilio.notify_by_phone(notification.listener)
            self.assertEqual(result['to'], notification.listener.userprofile.phone)
