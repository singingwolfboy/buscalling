from fixture import DataSet
import datetime
import os
from google.appengine.ext import db
from google.appengine.api.users import User

# need to set AUTH_DOMAIN before we can create User objects
if not 'AUTH_DOMAIN' in os.environ:
    from buscall.util import AUTH_DOMAIN
    os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
test_user = User("test@example.com")

class BusListenerData(DataSet):
    class morning_bus:
        user = test_user
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
        user = test_user
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
        user = test_user
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

class BusAlertData(DataSet):
    class cron_bus_20_min:
        listener = BusListenerData.cron_bus
        minutes = 20
        medium = "email"
        executed = False
