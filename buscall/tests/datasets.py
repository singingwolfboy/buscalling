from fixture import DataSet
import datetime
import os
from google.appengine.ext import db
from google.appengine.api.users import User

# need to set AUTH_DOMAIN before we can create User objects
if not 'AUTH_DOMAIN' in os.environ:
    from buscall.util import AUTH_DOMAIN
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN

class UserProfileData(DataSet):
    class test_profile:
        user = User("test@example.com")
        paid = True
        joined = datetime.datetime(2010, 2, 3, 10, 32, 45)
        last_login = datetime.datetime(2011, 7, 14, 7, 0, 0)

    class with_phone:
        user = User("phone@example.com")
        paid = True
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
        mon = True
        tue = True
        wed = True
        thu = True
        fri = True
        sat = False
        sun = False
        start = datetime.time(8, 0) # 8:00 AM
        seen = False

    class afternoon_bus:
        userprofile = UserProfileData.test_profile
        agency_id = "mbta"
        route_id = "59"
        direction_id = "59_590008v0_1"
        stop_id = "82048"
        mon = True
        tue = True
        wed = True
        thu = True
        fri = True
        sat = False
        sun = False
        start = datetime.time(16,45) # 4:45 PM
        seen = False

    class cron_bus:
        userprofile = UserProfileData.test_profile
        agency_id = "mbta"
        route_id = "26"
        direction_id = "26_1_var1"
        stop_id = "492"
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
        direction_id = "70_0_var1"
        stop_id = "88333"
        mon = True
        tue = False
        wed = True
        thu = False
        fri = True
        sat = False
        sun = True
        start = datetime.time(4,0)
        seen = True

class BusAlertData(DataSet):
    class cron_bus_20_min:
        listener = BusListenerData.cron_bus
        minutes = 20
        medium = "email"
        executed = False

    class seen_bus_email_alert:
        listener = BusListenerData.seen_bus
        minutes = 3
        medium = "email"
        executed = True

    class seen_bus_phone_alert:
        listener = BusListenerData.seen_bus
        minutes = 5
        medium = "phone"
        executed = False
