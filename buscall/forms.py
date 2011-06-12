import datetime
import time
from flask import request
from flaskext.wtf import Form, DecimalField, SelectField, BooleanField
from flaskext.wtf import HiddenInput, FieldList, FormField, IntegerField
from flaskext.wtf import Required, Optional
from wtforms.widgets import Input
from wtforms.fields import Field
from wtforms.validators import ValidationError
from flaskext.wtf.html5 import EmailField
from buscall.models.nextbus import NextbusError, AGENCIES, get_routes, get_route
from buscall.models.profile import days_of_week, alert_choices

class TimeInput(Input):
    input_type = "time"

time_formats = ['%H:%M']

class TimeField(Field):
    widget = TimeInput()

    def __init__(self, label=u'', validators=None, formats=time_formats, **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.formats = formats

    def _value(self):
        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.formats[0]) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)
            for format in self.formats:
                try:
                    timetuple = time.strptime(date_str, format)
                    # dropping DST info: timetuple.tm_isdst (fixme later)
                    self.data = datetime.time(*timetuple[3:6])
                    return
                except ValueError:
                    pass #try the next format
            # if we got here, we weren't able to serialize the data at all.
            self.data = None
            raise


class WaitlistForm(Form):
    email = EmailField(u'Email', validators=[Required()])
    location_lat  = DecimalField(u'Latitude', widget=HiddenInput(),
        validators=[Optional()])
    location_long = DecimalField(u'Longitude', widget=HiddenInput(),
        validators=[Optional()])

#    def validate_email(form, field):
#        if field.data == field.default:
#            field.message = u'%s cannot be %s' % (field.label.text, field.data)
#            raise ValidationError(field.message)

class AlertForm(Form):
    minutes = IntegerField(default=5)
    medium = SelectField(choices=alert_choices)

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(AlertForm, self).__init__(*args, **kwargs)

"""
class WeekForm(Form):
    sun = BooleanField()
    mon = BooleanField()
    tue = BooleanField()
    wed = BooleanField()
    thu = BooleanField()
    fri = BooleanField()
    sat = BooleanField()
    sun = BooleanField()

    def __init__(self, *args, **kwargs):
        kwargs['csrf_enabled'] = False
        super(WeekForm, self).__init__(*args, **kwargs)

    def validate(self, *args, **kwargs):
        success = super(WeekForm, self).validate(*args, **kwargs)
        if not any((self._fields[d].data for d in days_of_week)):
            self.errors
            self._errors["form"] = "At least one day of the week must be selected."
            success = False
        return success
"""

class RouteField(SelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(RouteField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data:
            try:
                routes = get_routes(form.agency_id.data)
                self.choices = [(id, i['title']) for id, i in routes.iteritems()]
            except NextbusError:
                pass
        super(RouteField, self).pre_validate(form)

class DirectionField(SelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(DirectionField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data and form.route_id.data:
            try:
                route_info = get_route(form.agency_id.data, form.route_id.data)
                self.choices = [(id, i['title']) for id, i in route_info['directions'].items()]
            except NextbusError:
                pass
        super(DirectionField, self).pre_validate(form)

class StopField(SelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(StopField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data and form.route_id.data and form.direction_id.data:
            agency = form.agency_id.data
            route = form.route_id.data
            direction = form.direction_id.data
            try:
                route_info = get_route(agency, route)
                self.choices = [(id, route_info['stops'][id]['title']) for id in route_info['directions'][direction]['stops']]
            except NextbusError:
                pass
        super(StopField, self).pre_validate(form)

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
    # week = FieldList(FormField(WeekForm), min_entries=1, max_entries=1)
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
        if not any((self._fields[d].data for d in days_of_week)):
            self.errors # generate the error dict
            self._errors["week"] = "At least one day of the week must be selected."
            success = False
        return success
