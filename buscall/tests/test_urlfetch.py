from __future__ import with_statement
import datetime
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.listener import BusListener, BusNotification
from buscall.models.profile import UserProfile
from buscall.views.tasks import poll
from buscall.credentials import ACCOUNT_SID
from buscall.tests.util import CustomTestCase
from google.appengine.ext import testbed

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
    class cron_bus:
        userprofile = UserProfileData.test_profile
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
        recur = True
        mon = False
        tue = False
        wed = False
        thu = False
        fri = False
        sat = True
        sun = True
        start = datetime.time(15,00) # 3:00 PM
        seen = False

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

class BusNotificationData(DataSet):
    class cron_bus_20_min:
        listener = BusListenerData.cron_bus
        minutes = 20
        medium = "email"
        executed = False

    class seen_bus_phone_notification:
        listener = BusListenerData.seen_bus
        minutes = 5
        medium = "phone"
        executed = False

class UrlfetchTestCase(CustomTestCase, DataTestCase):
    datasets = [UserProfileData, BusListenerData, BusNotificationData]

    def test_predictions(self):
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
        predictions = nextbus.get_predictions(agency_id, route_id, direction_id, stop_id)
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
        notification = BusNotification.gql("WHERE medium = :medium AND executed = False", medium="phone").fetch(1)[0]
        with app.test_request_context('/tasks/poll'):
            result = twilio.notify_by_phone(notification.listener)
            self.assertEqual(result['to'], notification.listener.userprofile.phone)
