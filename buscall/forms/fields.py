import datetime
import time
from ndb import Key
from wtforms.widgets import Input, TextInput
from wtforms.fields import Field
from flaskext.wtf import SelectField, TextField, RadioField
from buscall.models.nextbus import Agency, Route, Direction, Stop

__all__ = ['TelInput', 'TelephoneField', 'RadioBooleanField', 'TimeInput', 'TimeField', 'RouteField', 'DirectionField', 'StopField']

time_formats = ['%I:%M%p', '%I:%M %p', '%H:%M']

class TelInput(Input):
    input_type = "tel"

class TelephoneField(TextField):
    widget = TelInput()

class RadioBooleanField(RadioField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("coerce", bool)
        super(RadioField, self).__init__(*args, **kwargs)

    def process_formdata(self, valuelist):
        if not valuelist:
            self.data = False
        if valuelist[0].lower() in ['n', 'no', 'false', '0']:
            self.data = False
        else:
            self.data = True
    
    def iter_choices(self):
        for value, label in self.choices:
            if value:
                v = u"y"
            else:
                v = u"n"
            yield (v, label, self.coerce(value) == self.data)

def maybe_unicode(s):
    if s == None:
        return s
    return unicode(s)

class MaybeRadioField(RadioField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("coerce", maybe_unicode)
        super(MaybeRadioField, self).__init__(*args, **kwargs)
    
    def pre_validate(self, form):
        if self.data is None:
            return
        super(MaybeRadioField, self).pre_validate(form)

class MaybeSelectField(SelectField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("coerce", maybe_unicode)
        super(MaybeSelectField, self).__init__(*args, **kwargs)
    
    def pre_validate(self, form):
        if self.data is None:
            return
        super(MaybeSelectField, self).pre_validate(form)

class TimeInput(Input):
    input_type = "time"

class TimeField(Field):
    # widget = TimeInput()
    widget = TextInput()

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
                    pass  # try the next format
            # if we got here, we weren't able to serialize the data at all.
            self.data = None
            raise

class AgencyField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('', '')]
        super(AgencyField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        self.choices = [(agency.id, agency.name)
                for agency in
                Agency.query()]
        super(AgencyField, self).pre_validate(form)

class RouteField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('', '')]
        super(RouteField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        agency_id = form.agency_id.data
        if agency_id:
            agency_key = Key(Agency, agency_id)
            self.choices = [(route.id, route.name)
                    for route in
                    Route.query(Route.agency_key == agency_key)]
        super(RouteField, self).pre_validate(form)

class DirectionField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('', '')]
        super(DirectionField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        agency_id = form.agency_id.data
        route_id = form.route_id.data
        if agency_id and route_id:
            route_key = Key(Route, "{0}|{1}".format(agency_id, route_id))
            self.choices = [(direction.id, direction.name)
                    for direction in
                    Direction.query(Direction.route_key == route_key)]
        super(DirectionField, self).pre_validate(form)

class StopField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('', '')]
        super(StopField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        agency_id = form.agency_id.data
        route_id = form.route_id.data
        direction_id = form.direction_id.data
        if agency_id and route_id and direction_id:
            direction_key = Key(Direction, "{0}|{1}|{2}".format(agency_id, route_id, direction_id))
            self.choices = [(stop.id, stop.name)
                    for stop in
                    Stop.query(Stop.direction_key == direction_key)]
        super(StopField, self).pre_validate(form)
