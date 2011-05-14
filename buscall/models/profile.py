from google.appengine.api import users
from google.appengine.ext import db

class UserProfile(db.Model):
    user = db.UserProperty()

class BusListener(db.Model):
    user = db.UserProperty()

    # info about bus stop
    agency =   db.StringProperty(default="mbta")
    route_id = db.StringProperty()
    stop_id =  db.StringProperty()

    # when to start and stop listening
    start = db.TimeProperty()
    end   = db.TimeProperty()

    # day of week: since we'll be sorting by this,
    # it actually makes sense to keep them as separate properties
    mon = db.BooleanProperty()
    tue = db.BooleanProperty()
    wed = db.BooleanProperty()
    thu = db.BooleanProperty()
    fri = db.BooleanProperty()
    sat = db.BooleanProperty()
    sun = db.BooleanProperty()

