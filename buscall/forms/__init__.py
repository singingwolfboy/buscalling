from flask import g
from flaskext.wtf import Form, DecimalField, SelectField, BooleanField, TextField, HiddenField, RadioField
from flaskext.wtf import HiddenInput, FieldList, FormField, IntegerField
from flaskext.wtf import Required, Optional, Regexp, Length
from flaskext.wtf.html5 import EmailField
from buscall.forms.fields import TimeField, RouteField, DirectionField, StopField, TelephoneField, RadioBooleanField, MaybeRadioField
from buscall.models.listener import NOTIFICATION_CHOICES
from buscall.util import DAYS_OF_WEEK
import datetime

class WaitlistForm(Form):
    email = EmailField(u'Email', validators=[Required()])
    location_lat  = DecimalField(u'Latitude', widget=HiddenInput(),
        validators=[Optional()])
    location_long = DecimalField(u'Longitude', widget=HiddenInput(),
        validators=[Optional()])

class NotificationForm(Form):
    minutes = IntegerField(default=5)
    medium = SelectField(choices=NOTIFICATION_CHOICES)

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(NotificationForm, self).__init__(*args, **kwargs)

today = datetime.date.today()
this_week = [today + datetime.timedelta(days=n) for n in range(7)]
def weekday_choice_text_format(day):
    number = int(day.strftime("%d"))
    formatted = "%s %d" % (day.strftime("%a, %b"), number)
    if day == today:
        return formatted + " (today)"
    elif day == today + datetime.timedelta(days=1):
        return formatted + " (tomorrow)"
    else:
        return formatted
this_week_choices = [(day.strftime('%a').lower(), weekday_choice_text_format(day)) for day in this_week]


class BusListenerForm(Form):
    agency_id = SelectField("Agency", choices=[('', '')],
        id="agency", validators=[Required()])
    route_id = RouteField("Route",
        id="route", validators=[Required()])
    direction_id = DirectionField("Direction",
        id="direction", validators=[Required()])
    stop_id = StopField("Stop",
        id="stop", validators=[Required()])
    recur = RadioBooleanField("Repeat", choices=[(True, "Every Week"), (False, "Don't Repeat")], default=True)
    start = TimeField("Start Checking", validators=[Required()])
    notifications = FieldList(FormField(NotificationForm), min_entries=1)
    # day of week booleans used for recurring listeners
    mon = BooleanField(default=(today.weekday() == 0))
    tue = BooleanField(default=(today.weekday() == 1))
    wed = BooleanField(default=(today.weekday() == 2))
    thu = BooleanField(default=(today.weekday() == 3))
    fri = BooleanField(default=(today.weekday() == 4))
    sat = BooleanField(default=(today.weekday() == 5))
    sun = BooleanField(default=(today.weekday() == 6))
    # day of week radio used for one-time listeners
    #dow = MaybeRadioField(choices=[(day, day.capitalize()) for day in DAYS_OF_WEEK])
    dow = SelectField("Date", choices=this_week_choices, default=today.strftime('%a').lower())

    def __init__(self, *args, **kwargs):
        self.agency_id.choices = [('','')] + [(id, agency.title) for (id, agency) in g.AGENCIES.items()]
        super(BusListenerForm, self).__init__(*args, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(BusListenerForm, self).validate(*args, **kwargs)
        recur = self._fields["recur"].data
        if recur and not any((self._fields[d].data for d in DAYS_OF_WEEK)):
            self.errors # generate the error dict
            if not "week" in self._errors:
                self._errors["week"] = []
            self._errors["week"].append("Please select at least one day of the week.")
            success = False
        if not recur and (self._fields["dow"].data is None or self._fields["dow"].data == "None"):
            self.errors # generate the error dict
            if not "week" in self._errors:
                self._errors["week"] = []
            self._errors["week"].append("Please select exactly one day of the week.")
            success = False
        
        return success

tel_validator = Regexp(r"^[0-9 \-+()]+$", messages={"invalid": "Contains invalid characters."})

class UserProfileForm(Form):
    first_name = TextField(validators=[Optional()])
    last_name  = TextField(validators=[Optional()])
    phone = TelephoneField("Phone", validators=[Optional(), Length(min=7), tel_validator])
