import datetime
import time
from wtforms.widgets import Input
from wtforms.fields import Field
from flaskext.wtf import SelectField
from buscall.models.nextbus import NextbusError, AGENCIES, get_routes, get_route

__all__ = ['TimeInput', 'TimeField', 'RouteField', 'DirectionField', 'StopField']

time_formats = ['%H:%M']

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
