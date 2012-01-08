from google.appengine.api import mail
from ndb import model
from buscall.models.nextbus import BusPrediction
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

class ScheduledNotification(model.Model):
    minutes_before = model.IntegerProperty(required=True)
    medium = model.StringProperty(choices=[k for k, v in NOTIFICATION_CHOICES], required=True)
    has_executed = model.BooleanProperty(default=False)

    def __str__(self):
        if self.has_executed:
            status = "executed"
        else:
            status = "not executed"
        return "%s %d minutes before via %s, %s" % \
            (self.__class__.__name__, self.minutes_before, self.medium, status)

    def notify(self, listener, prediction):
        minutes = getattr(prediction, "minutes", None) or self.minutes_before

        if self.medium == "email":
            notify_by_email(listener, minutes)
        elif self.medium == "phone":
            notify_by_phone(listener, minutes)
        elif self.medium == "txt":
            notify_by_txt(listener, minutes)
        else:
            raise NotImplementedError

        self.has_executed = True
        self.put()

class BusListener(model.Model):
    profile_key = model.KeyProperty(required=True)
    enabled = model.BooleanProperty(default=True)

    # info about bus stop
    agency_key = model.KeyProperty(required=True)
    route_key = model.KeyProperty(required=True)
    direction_key = model.KeyProperty(required=True)
    stop_key = model.KeyProperty(required=True)

    # the scheduled notifications themselves
    scheduled_notifications = model.StructuredProperty(
            ScheduledNotification, repeated=True)

    # is this a one-time alert, or a recurring alert?
    recur = model.BooleanProperty(required=True)

    # when to start listening
    # App Engine doesn't allow inequality filters on multiple entities
    # (such as time is after start and time is before end)
    # so instead we use a booleans on listeners to determine if
    # they need to be checked.
    start = model.TimeProperty(required=True)

    # day of week: since we'll be sorting by this,
    # it actually makes sense to keep them as separate properties
    mon = model.BooleanProperty(default=True)
    tue = model.BooleanProperty(default=True)
    wed = model.BooleanProperty(default=True)
    thu = model.BooleanProperty(default=True)
    fri = model.BooleanProperty(default=True)
    sat = model.BooleanProperty(default=True)
    sun = model.BooleanProperty(default=True)

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

            day_names = [day.capitalize() for day in DAYS_OF_WEEK]
            day_vals = [getattr(self, day) for day in DAYS_OF_WEEK]
            if not any(day_vals):
                return "never"  # should never get here
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
            return "never"  # should never get here

    @property
    def agency(self):
        return self.agency_key.get()
    @property
    def route(self):
        return self.route_key.get()
    @property
    def direction(self):
        return self.direction_key.get()
    @property
    def stop(self):
        return self.stop_key.get()

    @property
    def id(self):
        return self.key.id()

    def get_predictions(self):
        "Use the Nextbus API to get route prediction information."
        return BusPrediction.query(
            agency_key = self.agency_key,
            route_key = self.route_key,
            direction_key = self.direction_key,
            stop_key = self.stop_key)

    def fire_notifications(self, minutes=None):
        "minutes parameter is the actual prediction time"
        profile = self.profile_key.get()
        if not profile.subscribed and profile.credits < 1:
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
