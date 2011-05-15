from google.appengine.api import users
from google.appengine.ext import db
try:
    from itertools import compress
except ImportError:
    from itertools import izip
    def compress(data, selectors):
        return (d for d, s in izip(data, selectors) if s)

days_of_week = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']

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

    @property
    def daily(self):
        return all((getattr(self, d) for d in days_of_week)

    @property
    def weekdays(self):
        return all((getattr(self, d) for d in days_of_week[0:5])

    @property
    def weekends(self):
        return all((getattr(self, d) for d in days_of_week[-2:])

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

    
        

