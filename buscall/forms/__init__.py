from flaskext.wtf import Form, DecimalField, SelectField, BooleanField, TextField, HiddenField, RadioField
from flaskext.wtf import HiddenInput, FieldList, FormField, IntegerField
from flaskext.wtf import Required, Optional, Regexp, Length
from flaskext.wtf.html5 import EmailField
from buscall.forms.fields import TimeField, RouteField, DirectionField, StopField, TelephoneField, RadioBooleanField, MaybeRadioField
from buscall.models.nextbus import AGENCIES
from buscall.models.listener import ALERT_CHOICES
from buscall.util import DAYS_OF_WEEK

class WaitlistForm(Form):
    email = EmailField(u'Email', validators=[Required()])
    location_lat  = DecimalField(u'Latitude', widget=HiddenInput(),
        validators=[Optional()])
    location_long = DecimalField(u'Longitude', widget=HiddenInput(),
        validators=[Optional()])

class AlertForm(Form):
    minutes = IntegerField(default=5)
    medium = SelectField(choices=ALERT_CHOICES)

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(AlertForm, self).__init__(*args, **kwargs)

agency_choices = [('','')] + [(id, agency.title) for (id, agency) in AGENCIES.items()]

class BusListenerForm(Form):
    agency_id = SelectField("Agency", choices=agency_choices,
        id="agency", validators=[Required()])
    route_id = RouteField("Route",
        id="route", validators=[Required()])
    direction_id = DirectionField("Direction",
        id="direction", validators=[Required()])
    stop_id = StopField("Stop",
        id="stop", validators=[Required()])
    recur = RadioBooleanField(choices=[(True, "Recurring"), (False, "One Time")], default=True)
    start = TimeField("Start Checking", validators=[Required()])
    alerts = FieldList(FormField(AlertForm), min_entries=1)
    # day of week booleans used for recurring listeners
    sun = BooleanField()
    mon = BooleanField()
    tue = BooleanField()
    wed = BooleanField()
    thu = BooleanField()
    fri = BooleanField()
    sat = BooleanField()
    sun = BooleanField()
    # day of week radio used for one-time listeners
    dow = MaybeRadioField(choices=[(day, day.capitalize()) for day in DAYS_OF_WEEK])


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