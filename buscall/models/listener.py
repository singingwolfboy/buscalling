from google.appengine.api import users, mail
from google.appengine.ext import db
from buscall.models.nextbus import AGENCIES, get_predictions, get_route
from buscall.models.profile import UserProfile
from buscall.util import DAYS_OF_WEEK, MAIL_SENDER
from buscall.models.twilio import notify_by_phone, notify_by_txt
from buscall.decorators import check_user_payment
from buscall.util import humanize_list
import datetime
try:
    from itertools import compress
except ImportError:
    from itertools import izip
    def compress(data, selectors):
        return (d for d, s in izip(data, selectors) if s)

NOTIFICATION_CHOICES = (('phone', 'Call'), ('txt', 'Text'), ('email', 'Email'))

class BusListener(db.Model):
    userprofile = db.ReferenceProperty(UserProfile, collection_name="listeners", required=True)

    # info about bus stop
    agency_id = db.StringProperty(required=True, default="mbta")
    route_id = db.StringProperty(required=True)
    direction_id = db.StringProperty(required=False)
    stop_id = db.StringProperty(required=True)

    # is this a one-time alert, or a recurring alert?
    recur = db.BooleanProperty(required=True)

    # when to start listening
    # App Engine doesn't allow inequality filters on multiple entities
    # (such as time is after start and time is before end)
    # so instead we'll use a boolean to determine whether this needs to be checked
    start = db.TimeProperty(required=True)
    # when all your notifications have been satisfied, set seen=True
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
        return self.mon and self.tue and self.wed and self.thu and self.fri \
            and not self.sat and not self.sun

    @property
    def weekends(self):
        return self.sat and self.sun \
            and not self.mon and not self.tue and not self.wed and not self.thu and not self.fri

    @property
    def repeat_descriptor(self):
        if self.recur:
            if self.daily:
                return "every day"
            if self.weekdays:
                return "every weekday"
            if self.weekends:
                return "every weekend"
            
            day_names =  [day.capitalize() for day in DAYS_OF_WEEK]
            day_vals = [getattr(self, day) for day in DAYS_OF_WEEK]
            if not any(day_vals):
                return "never" # should never get here
            return "every %s" % (humanize_list(compress(day_names, day_vals)),)
        
        else:
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            for i, day in enumerate(DAYS_OF_WEEK):
                if getattr(self, day):
                    if i == today.weekday():
                        return "today"
                    if i == tomorrow.weekday():
                        return "tomorrow"
                    return "on %s" % (day.capitalize())
            return "never" # should never get here
    
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
    
    @property
    def id(self):
        return self.key().id()
    
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
        values[u'user'] = self.userprofile.user
        values[u'repeat'] = self.repeat_descriptor
        return "%(class)s for %(user)s: %(agency_id)s %(route_id)s " \
            "%(direction_id)s %(stop_id)s %(start)s %(repeat)s" \
            % values
    
    def get_predictions(self):
        "Use the Nextbus API to get route prediction information."
        return get_predictions(self.agency_id, self.route_id, self.direction_id, self.stop_id)
    
    def check_notifications(self):
        self.seen = all((notification.executed for notification in self.notifications))
        if self.seen and not self.recur:
            self.delete()
        else:
            self.put()
    
    def delete(self):
        # delete all your associated notifications first
        for notification in self.notifications:
            notification.delete()
        # and then delete yourself
        super(BusListener, self).delete()

class BusNotification(db.Model):
    listener = db.ReferenceProperty(BusListener, collection_name="notifications", required=True)
    minutes = db.IntegerProperty(required=True)
    medium = db.StringProperty(choices=[k for k,v in NOTIFICATION_CHOICES], required=True)
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
        userprofile = self.listener.userprofile
        if not userprofile.subscribed and userprofile.credits < 1:
            # no money, no notification
            return

        if minutes is None:
            minutes = self.minutes

        if self.medium == "email":
            notify_by_email(self.listener, minutes)
        elif self.medium == "phone":
            notify_by_phone(self.listener, minutes)
        elif self.medium == "txt":
            notify_by_txt(self.listener, minutes)
        else:
            raise NotImplementedError
        
        self.executed = True
        self.put()
        self.listener.check_notifications()

@check_user_payment
def notify_by_email(listener, minutes=None):
    if minutes is None:
        predictions = listener.get_predictions()
        minutes = predictions.buses[0].minutes
    subject = "ALERT: %s bus, %s" % (listener.route.title, listener.stop.title)
    body = "Your bus is coming in %d minutes." % (minutes)
    mail.send_mail(sender=MAIL_SENDER,
        to=listener.userprofile.email,
        subject=subject, body=body)
