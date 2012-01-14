from __future__ import with_statement
from ndb import Key
from buscall import app
from buscall.models import nextbus, twilio
from buscall.models.listener import BusListener, ScheduledNotification
from buscall.models.user import User
from buscall.models.nextbus import Agency, Route, Direction, Stop
from buscall.views.tasks import reset_seen_flags
from tests.util import CustomTestCase

from fixture import DataSet, DataTestCase
import datetime

class UserData(DataSet):
    class test_user:
        primary_email = "test@example.com"
        subscribed = True
        credits = 8
        joined = datetime.datetime(2010, 2, 3, 10, 32, 45)
        last_login = datetime.datetime(2011, 7, 14, 7, 0, 0)

    class with_phone:
        primary_email = "phone@example.com"
        subscribed = True
        credits = 0
        phone = "999-888-7777"
        joined = datetime.datetime(2011, 2, 9, 10, 11, 12)
        last_login = datetime.datetime(2011, 6, 10, 10, 15)

class BusListenerData(DataSet):
    class morning_bus:
        user_key = UserData.test_user
        agency_key = Key(Agency, "mbta")
        route_key = Key(Route, "mbta|556")
        direction_key = Key(Direction, "mbta|556|556_5560006v0_1")
        stop_key = Key(Stop, "mbta|556|556_5560006v0_1|77378")
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
        userprofile = UserData.with_phone
        agency_key = Key(Agency, "mbta")
        route_key = Key(Route, "mbta|70")
        direction_key = Key(Direction, "mbta|70|70_1_var0")
        stop_key = Key(Stop, "mbta|70|70_1_var0|88333")
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

class ScheduledNotificationData(DataSet):
    class morning_bus_20_min:
        minutes_before = 20
        medium = "email"
        has_executed = False

    class seen_bus_email_notification:
        minutes_before = 3
        medium = "email"
        has_executed = True

    class seen_bus_phone_notification:
        minutes_before = 5
        medium = "phone"
        has_executed = False

# class DatastoreTestCase(CustomTestCase, DataTestCase):
#     datasets = [UserData, BusListenerData, ScheduledNotificationData]
