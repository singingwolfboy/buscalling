from google.appengine.api import users, mail
from google.appengine.ext import db
from buscall.models.nextbus import AGENCIES, get_predictions, get_route
from buscall.util import DAYS_OF_WEEK, MAIL_SENDER
try:
    from itertools import compress
except ImportError:
    from itertools import izip
    def compress(data, selectors):
        return (d for d, s in izip(data, selectors) if s)

ALERT_CHOICES = (('phone', 'Phone'), ('txt', 'Text'), ('email', 'Email'))

class BusListener(db.Model):
    user = db.UserProperty(required=True)

    # info about bus stop
    agency_id = db.StringProperty(required=True, default="mbta")
    route_id = db.StringProperty(required=True)
    direction_id = db.StringProperty(required=False)
    stop_id = db.StringProperty(required=True)

    # when to start listening
    # App Engine doesn't allow inequality filters on multiple entities
    # (such as time is after start and time is before end)
    # so instead we'll use a boolean to determine whether this needs to be checked
    start = db.TimeProperty(required=True)
    # when all your alerts have been satisfied, set seen=True
    seen  = db.BooleanProperty(required=True, default=False)

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
        return all((getattr(self, d) for d in DAYS_OF_WEEK))

    @property
    def weekdays(self):
        return all((getattr(self, d) for d in DAYS_OF_WEEK[0:5]))

    @property
    def weekends(self):
        return all((getattr(self, d) for d in DAYS_OF_WEEK[-2:]))

    @property
    def repeat_descriptor(self):
        if(self.daily):
            return "daily"

        day_names =  [d.capitalize() for d in DAYS_OF_WEEK]
        day_vals = [getattr(self, d) for d in DAYS_OF_WEEK]
        if(self.weekdays):
            days = list(compress(day_names[-2], day_vals[-2:]))
            days.insert(0, "weekdays")
        elif(self.weekends):
            days = list(compress(day_names[0:4], day_vals[0:5]))
            days.insert(0, "weekends")
        else:
            days = compress(day_names, day_vals)

        return ", ".join(days)
    
    @property
    def agency(self):
        return AGENCIES[self.agency_id]
    
    @property
    def route(self):
        if not getattr(self, "_route", None):
            self._route = get_route(self.agency_id, self.route_id, use_dicts=True)
        return self._route
    
    @property
    def direction(self):
        return self.route.directions[self.direction_id]
    
    @property
    def stop(self):
        return self.route.stops[self.stop_id]
    
    def __str__(self):
        values = {}
        for prop in self.properties().keys():
            values[prop] = getattr(self, prop, None)
        for time in [u'start']:
            try:
                values[time] = values[time].time()
            except AttributeError:
                pass
        values[u'class'] = self.__class__.__name__
        values[u'repeat'] = self.repeat_descriptor
        return "%(class)s for %(user)s: %(agency_id)s %(route_id)s " \
            "%(direction_id)s %(stop_id)s %(start)s %(repeat)s" \
            % values
    
    def get_predictions(self):
        "Use the Nextbus API to get route prediction information."
        return get_predictions(self.agency_id, self.route_id, self.direction_id, self.stop_id)

class BusAlert(db.Model):
    listener = db.ReferenceProperty(BusListener, collection_name="alerts", required=True)
    minutes = db.IntegerProperty(required=True)
    medium = db.StringProperty(choices=[k for k,v in ALERT_CHOICES], required=True)
    executed = db.BooleanProperty(required=True, default=False)

    def __str__(self):
        if self.executed:
            status = "executed"
        else:
            status = "not executed"
        return "%s for <%s>, %d minutes before via %s, %s" % \
            (self.__class__.__name__, self.listener, self.minutes, self.medium, status)

    def execute(self, minutes=None):
        "minutes parameter is the actual prediction time"
        route = self.listener.route
        stop = self.listener.stop
        if minutes is None:
            minutes = self.minutes

        if self.medium == "email":
            subject = "ALERT: %s bus, %s" % (route.title, stop.title)
            body = "Your bus is coming in %d minutes." % (minutes)
            mail.send_mail(sender=MAIL_SENDER,
                to=self.listener.user.email(),
                subject=subject, body=body)
        else:
            raise NotImplementedError
        
        self.executed = True
