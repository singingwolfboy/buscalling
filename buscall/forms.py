import datetime
import time
from flaskext.wtf import Form, DecimalField, SelectField, BooleanField
from flaskext.wtf import HiddenInput
from flaskext.wtf import Required, Optional
from wtforms.widgets import Input
from wtforms.fields import Field
from flaskext.wtf.html5 import EmailField
from models.nextbus import get_all_routes

class TimeInput(Input):
    input_type = "time"

class TimeField(Field):
    widget = TimeInput()

    def __init__(self, label=u'', validators=None, format='%H:%M:%S', **kwargs):
        super(TimeField, self).__init__(label, validators, **kwargs)
        self.format = format

        if self.raw_data:
            return u' '.join(self.raw_data)
        else:
            return self.data and self.data.strftime(self.format) or u''

    def process_formdata(self, valuelist):
        if valuelist:
            date_str = u' '.join(valuelist)
            try:
                timetuple = time.strptime(date_str, self.format)
                self.data = datetime.datetime(*timetuple[:6])
            except ValueError:
                self.data = None
                raise


class WaitlistForm(Form):
    email = EmailField(u'Email', default='email@example.com',
        validators=[Required()])
    location_lat  = DecimalField(u'Latitude', widget=HiddenInput(),
        validators=[Optional()])
    location_long = DecimalField(u'Longitude', widget=HiddenInput(),
        validators=[Optional()])

    def validate_email(form, field):
        if field.data == field.default:
            field.message = u'%s cannot be %s' % (field.label.text, field.data)
            raise v.ValidationError(field.message)

#routes = [(r['title'], r['tag']) for r in get_all_routes()['stops'] ]
routes = [('1', '1'), ('556', '556')]

class BusListenerForm(Form):
    route_id = SelectField(routes)
    stop_id = SelectField()
    start = TimeField(validators=[Required()])
    end = TimeField(validators=[Required()])
    mon = BooleanField()
    tue = BooleanField()
    wed = BooleanField()
    thu = BooleanField()
    fri = BooleanField()
    sat = BooleanField()
    sun = BooleanField()
