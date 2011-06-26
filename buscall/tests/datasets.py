from fixture import DataSet
import datetime
from google.appengine.ext import db
from google.appengine.api import users

test_user = users.User("test@example.com")

class BusListenerData(DataSet):
    class morning_bus:
        user = test_user
        agency_id = "MBTA"
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
        end   = datetime.time(8,30) # 8:30 AM

    class afternoon_bus:
        user = test_user
        agency_id = "MBTA"
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
        end   = datetime.time(17,10) # 5:10 PM
