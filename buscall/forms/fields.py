import datetime
import time
from ndb import Key
from itertools import izip
from wtforms.widgets import Input, TextInput, RadioInput, ListWidget
from wtforms.fields import Field, FieldList, _unset_value
from flaskext.wtf import SelectField, TextField, BooleanField, RadioField
from buscall.models.nextbus_api import NextbusError
from buscall.models.nextbus import Agency, Route

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
                    pass #try the next format
            # if we got here, we weren't able to serialize the data at all.
            self.data = None
            raise

class RouteField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(RouteField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        agency_id = form.agency_id.data
        if agency_id:
            try:
                agency = Key(Agency, agency_id).get()
                choices = []
                for route_id in agency.route_ids:
                    route = Key(Route, route_id).get()
                    choices.append((route.id, route.title))
                self.choices = choices
            except NextbusError:
                pass
        super(RouteField, self).pre_validate(form)

class DirectionField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(DirectionField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data and form.route_id.data:
            try:
                route = Key(Route, form.route_id.data).get()
                self.choices = [(d.id, d.title) for d in route.directions]
            except NextbusError:
                pass
        super(DirectionField, self).pre_validate(form)

class StopField(MaybeSelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(StopField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data and form.route_id.data and form.direction_id.data:
            agency_id = form.agency_id.data
            route_id = form.route_id.data
            direction_id = form.direction_id.data
            try:
                route = Key(Route, route_id).get()
                self.choices = [(id, route.stops[id].title) for id in route.directions[direction_id].stop_ids]
            except NextbusError:
                pass
        super(StopField, self).pre_validate(form)
