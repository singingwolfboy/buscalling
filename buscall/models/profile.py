from google.appengine.api import users
from google.appengine.ext import db
try:
    from itertools import compress
except ImportError:
    from itertools import izip
    def compress(data, selectors):
        return (d for d, s in izip(data, selectors) if s)

ALERT_CHOICES = (('phone', 'Phone'), ('txt', 'Text'), ('email', 'Email'))

class UserProfile(db.Model):
    user = db.UserProperty(required=True)

class BusListener(db.Model):
    user = db.UserProperty(required=True)

    # info about bus stop
    agency_id = db.StringProperty(required=True, default="mbta")
    route_id = db.StringProperty(required=True)
    direction_id = db.StringProperty(required=False)
    stop_id = db.StringProperty(required=True)

    # when to start and stop listening
    start = db.TimeProperty(required=True)
    end   = db.TimeProperty(required=True)

    # day of week: since we'll be sorting by this,
    # it actually makes sense to keep them as separate properties
    mon = db.BooleanProperty(required=True, default=True)
    tue = db.BooleanProperty(required=True, default=True)
    wed = db.BooleanProperty(required=True, default=True)
    thu = db.BooleanProperty(required=True, default=True)
    fri = db.BooleanProperty(required=True, default=True)
    sat = db.BooleanProperty(required=True, default=True)
    sun = db.BooleanProperty(required=True, default=True)

    @property
    def daily(self):
        return all((getattr(self, d) for d in days_of_week))

    @property
    def weekdays(self):
        return all((getattr(self, d) for d in days_of_week[0:5]))

    @property
    def weekends(self):
        return all((getattr(self, d) for d in days_of_week[-2:]))

    @property
    def repeat_descriptor(self):
        if(self.daily):
            return "daily"

        day_names =  [d.capitalize() for d in days_of_week]
        day_vals = [getattr(self, d) for d in days_of_week]
        if(self.weekdays):
            days = list(compress(day_names[-2], day_vals[-2:]))
            days.insert(0, "weekdays")
        elif(self.weekends):
            days = list(compress(day_names[0:4], day_vals[0:5]))
            days.insert(0, "weekends")
        else:
            days = compress(day_names, day_vals)

        return ", ".join(days)

class BusAlert(db.Model):
    listener = db.ReferenceProperty(BusListener, collection_name="alerts", required=True)
    minutes = db.IntegerProperty(required=True)
    medium = db.StringProperty(choices=[k for k,v in ALERT_CHOICES], required=True)
