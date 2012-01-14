from tests.util import CustomTestCase
import datetime
from ndb import Key
from buscall import app
from buscall.models import twilio
from buscall.models.nextbus import Agency, Route, Direction, Stop, BusPrediction
from buscall.models.user import User
from buscall.models.listener import BusListener, ScheduledNotification
from buscall.views.tasks import poll
from buscall.credentials import ACCOUNT_SID
from google.appengine.ext import testbed

class UrlfetchTestCase(CustomTestCase):
    def setUp(self):
        super(UrlfetchTestCase, self).setUp()
        mbta = Agency(id="mbta",
                name="MBTA",
                route_keys = [Key(Route, "mbta|26"), Key(Route, "mbta|70")])
        mbta_key = mbta.put()
        r26 = Route(id="mbta|26",
                name="26",
                agency_key=mbta_key,
                direction_keys=[Key(Direction, "mbta|26|26_1_var1")])
        r26_key = r26.put()
        r70 = Route(id="mbta|70",
                name="70",
                agency_key=mbta_key,
                direction_keys=[Key(Direction, "mbta|70|70_1_var0")])
        r70_key = r70.put()
        outbound = Direction(id="mbta|26|26_1_var1",
                name="outbound",
                agency_key=mbta_key,
                route_key=r26_key,
                stop_keys=[Key(Stop, "mbta|26|26_1_var1|492")])
        outbound_key = outbound.put()
        inbound = Direction(id="mbta|70|70_1_var0",
                name="inbound",
                agency_key=mbta_key,
                route_key=r70_key,
                stop_keys=[Key(Stop, "mbta|70|70_1_var0|88333")])
        inbound_key = inbound.put()
        my_house = Stop(id="mbta|26|26_1_var1|492",
                name="my house",
                agency_key=mbta_key,
                route_key=r26_key,
                direction_key=outbound_key)
        my_house_key = my_house.put()
        your_house = Stop(id="mbta|70|70_1_var0|88333",
                name="your house",
                agency_key=mbta_key,
                route_key=r70_key,
                direction_key=inbound_key)
        your_house_key = your_house.put()

        test_user = User(
                primary_email="test@example.com",
                subscribed=True,
                credits=8,
                joined=datetime.datetime(2010, 2, 3, 10, 32, 45),
                last_access=datetime.datetime(2011, 7, 14, 7, 0, 0))
        test_user_key = test_user.put()
        test_user_phone = User(
                primary_email="phone@example.com",
                subscribed=True,
                credits=0,
                phone="999-888-7777",
                joined=datetime.datetime(2011, 2, 9, 10, 11, 12),
                last_access=datetime.datetime(2011, 6, 10, 10, 15))
        test_user_phone_key = test_user_phone.put()

        notify_email = ScheduledNotification(
                minutes_before=20,
                medium="email",
                has_executed=False)
        notify_phone = ScheduledNotification(
                minutes_before=5,
                medium="phone",
                has_executed=False)
        cron_bus = BusListener(
                user_key=test_user_key,
                agency_key=mbta_key,
                route_key=r26_key,
                direction_key=outbound_key,
                stop_key=my_house_key,
                recur=True,
                sat=True,
                sun=True,
                start = datetime.time(15, 00), # 3:00 PM
                scheduled_notifications=[notify_email])
        cron_bus_key = cron_bus.put()
        another_bus = BusListener(
                user_key=test_user_phone_key,
                agency_key=mbta_key,
                route_key=r70_key,
                direction_key=outbound_key,
                stop_key=your_house_key,
                recur=True,
                mon=True,
                wed=True,
                fri=True,
                sun=True,
                start=datetime.time(4, 0),
                scheduled_notifications=[notify_phone])
        another_bus_key = another_bus.put()

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
