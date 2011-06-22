from flaskext.wtf import Form, DecimalField, SelectField, BooleanField
from flaskext.wtf import HiddenInput, FieldList, FormField, IntegerField
from flaskext.wtf import Required, Optional
from flaskext.wtf.html5 import EmailField
from buscall.forms.fields import TimeField, RouteField, DirectionField, StopField
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

class BusListenerForm(Form):
    agency_id = SelectField("Agency", choices=[('', '')] + [(key, val) for (key, val) in AGENCIES.items()],
        id="agency", validators=[Required()])
    route_id = RouteField("Route",
        id="route", validators=[Required()])
    direction_id = DirectionField("Direction",
        id="direction", validators=[Required()])
    stop_id = StopField("Stop",
        id="stop", validators=[Required()])
    start = TimeField("Start Checking", validators=[Required()])
    end = TimeField("Stop Checking", validators=[Required()])
    alerts = FieldList(FormField(AlertForm), min_entries=1)
    sun = BooleanField()
    mon = BooleanField()
    tue = BooleanField()
    wed = BooleanField()
    thu = BooleanField()
    fri = BooleanField()
    sat = BooleanField()
    sun = BooleanField()

    def validate(self, *args, **kwargs):
        success = super(BusListenerForm, self).validate(*args, **kwargs)
        if not any((self._fields[d].data for d in DAYS_OF_WEEK)):
            self.errors # generate the error dict
            self._errors["week"] = "At least one day of the week must be selected."
            success = False
        return success
