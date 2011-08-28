import datetime
import time
from itertools import izip
from wtforms.widgets import Input, RadioInput, ListWidget
from wtforms.fields import Field, FieldList, _unset_value
from flaskext.wtf import SelectField, TextField, BooleanField
from buscall.models.nextbus import NextbusError, AGENCIES, get_routes, get_route

__all__ = ['TelInput', 'TelephoneField', 'RadioBooleanField', 'TimeInput', 'TimeField', 'RouteField', 'DirectionField', 'StopField']

time_formats = ['%H:%M']

class TelInput(Input):
    input_type = "tel"

class TelephoneField(TextField):
    widget = TelInput()

class RadioBooleanField(BooleanField, SelectField):
    widget = ListWidget()
    option_widget = RadioInput()

    def __init__(self, label=None, validators=None, choices=((True, "True"), (False, "False")), **kwargs):
        SelectField.__init__(self, label, validators, bool, choices, **kwargs)
        self.data = None
    
    def __iter__(self):
        opts = dict(widget=self.option_widget, _name=self.name, _form=None)
        for value, label in self.choices:
            if value == None:
                id_type = "none"
            else:
                id_type = str(bool(value)).lower() # "true" or "false"
            bf = BooleanField(label=label, id=u'%s-%s' % (self.id, id_type), **opts)
            bf.process(None, value)
            if value == self.default:
                bf.checked = True
            else:
                bf.checked = False
            yield bf

    def process_formdata(self, valuelist):
        if valuelist:
            try:
                self.data = self.coerce(valuelist[0])
            except ValueError:
                raise ValueError(self.gettext(u'Invalid Choice: could not coerce'))

class TimeInput(Input):
    input_type = "time"

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

class RouteField(SelectField):
    def __init__(self, *args, **kwargs):
        if not 'choices' in kwargs:
            kwargs['choices'] = [('','')]
        super(RouteField, self).__init__(*args, **kwargs)

    def pre_validate(self, form):
        if form.agency_id.data:
            try:
                routes = get_routes(form.agency_id.data)
                self.choices = [(id, route.title) for id, route in routes.iteritems()]
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
                self.choices = [(d.id, d.title) for d in route_info.directions]
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
            agency_id = form.agency_id.data
            route_id = form.route_id.data
            direction_id = form.direction_id.data
            try:
                route = get_route(agency_id, route_id, use_dicts=True)
                self.choices = [(id, route.stops[id].title) for id in route.directions[direction_id].stop_ids]
            except NextbusError:
                pass
        super(StopField, self).pre_validate(form)
