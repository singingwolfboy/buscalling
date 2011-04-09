#from buscall.models import WaitlistEntry
#from .widgets import GeoPtHiddenInput, ModelConverter
#from wtforms.ext.appengine.db import model_form
from wtforms.form import Form
from wtforms import fields as f
from wtforms import validators as v
from wtforms import widgets as w

# split location hidden fields is too hard for WTForms, we'll handle separately
#WaitlistForm = model_form(WaitlistEntry, exclude=('location'), field_args={
#    'email': {
#        'default': 'email@example.com',
#    }
#})

class WaitlistForm(Form):
    email = f.TextField(u'Email', default='email@example.com',
        validators=[v.required(), v.email()])
    location_lat  = f.DecimalField(u'Latitude', widget=w.HiddenInput(),
        validators=[v.optional()])
    location_long = f.DecimalField(u'Longitude', widget=w.HiddenInput(),
        validators=[v.optional()])

    def validate_email(form, field):
        if field.data == field.default:
            field.message = u'%s cannot be %s' % (field.label.text, field.data)
            raise v.ValidationError(field.message)