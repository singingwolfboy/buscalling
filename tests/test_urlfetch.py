from tests.util import CustomTestCase
import datetime
from ndb import Key
from buscall import app
from buscall.models import twilio
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction
from buscall.models.user import User
from buscall.models.listener import BusListener
from buscall.views.tasks import poll
from buscall.credentials import ACCOUNT_SID
from google.appengine.ext import testbed

from fixture import DataSet, DataTestCase

class AgencyData(DataSet):
    class mbta:
        id = "mbta"
        name = "MBTA"
        # route_keys = [RouteData.r26, RouteData.r70]

class RouteData(DataSet):
    class r26:
        id = "mbta|26"
        name = "26"
        agency_key = AgencyData.mbta
        # direction_keys = [DirectionData.inbound]

    class r70:
        id = "mbta|70"
        name = "70"
        agency_key = AgencyData.mbta
        # direction_keys = [DirectionData.outbound]

AgencyData.mbta.route_keys = [RouteData.r26, RouteData.r70]

class DirectionData(DataSet):
    class inbound:
        id = "mbta|26|26_1_var1"
        name = "inbound"
        agency_key = AgencyData.mbta
        route_key = RouteData.r26

    class outbound:
        id = "mbta|70|70_1_var0"
        name = "outbound"
        agency_key = AgencyData.mbta
        route_key = RouteData.r70

RouteData.r26.direction_keys = [DirectionData.inbound]
RouteData.r70.direction_keys = [DirectionData.outbound]

class StopData(DataSet):
    class my_house:
        id = "mbta|26|26_1_var1|492"
        name = "my house"
        agency_key = AgencyData.mbta
        route_key = RouteData.r26
        direction_key = DirectionData.inbound

    class your_house:
        id = "mbta|70|70_1_var0|88333"
        name = "your house"
        agency_key = AgencyData.mbta
        route_key = RouteData.r70
        direction_key = DirectionData.outbound

DirectionData.inbound.stop_keys = [StopData.my_house]
DirectionData.outbound.stop_keys = [StopData.your_house]

class UserData(DataSet):
    class test_user:
        primary_email = "test@example.com"
        subscribed = True
        credits = 8
        joined = datetime.datetime(2010, 2, 3, 10, 32, 45)
        last_access = datetime.datetime(2011, 7, 14, 7, 0, 0)

    class with_phone:
        primary_email = "phone@example.com"
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

    class phone_notification:
        minutes_before = 5
        medium = "phone"
        has_executed = False

class BusListenerData(DataSet):
    class cron_bus:
        user_key = UserData.test_user
        agency_key = AgencyData.mbta
        route_key = RouteData.r26
        direction_key = DirectionData.inbound
        stop_key = StopData.my_house
        recur = True
        mon = False
        tue = False
        wed = False
        thu = False
        fri = False
        sat = True
        sun = True
        start = datetime.time(15,00) # 3:00 PM
        scheduled_notifications = [ScheduledNotificationData.cron_bus_20_min]

    class another_bus:
        user_key = UserData.with_phone
        agency_key = AgencyData.mbta
        route_key = RouteData.r70
        direction_key = DirectionData.outbound
        stop_key = StopData.your_house
        recur = True
        mon = True
        tue = False
        wed = True
        thu = False
        fri = True
        sat = False
        sun = True
        start = datetime.time(4,0)
        scheduled_notifications = [ScheduledNotificationData.phone_notification]

class UrlfetchTestCase(CustomTestCase, DataTestCase):
    datasets = [UserData, BusListenerData] #  , ScheduledNotificationData]

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
            poll(quiet_moment)
            messages = mail_stub.get_sent_messages()
            self.assertEqual(len(messages), 0)
    
    def test_cron_with_listeners(self):
        mail_stub = self.testbed.get_stub(testbed.MAIL_SERVICE_NAME)
        active_moment = datetime.datetime(2011, 7, 2, 15, 10, 24) # 3:10:24 on Sat, July 2
        with app.test_request_context('/tasks/poll'):
            poll(active_moment)
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
        listener = BusListener.query(
                BusListener.scheduled_notifications.medium == "phone",
                BusListener.scheduled_notifications.has_executed == False).get()
        with app.test_request_context('/tasks/poll'):
            result = twilio.notify_by_phone(listener)
            self.assertEqual(result['to'], listener.user.phone)
