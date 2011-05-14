from flaskext.wtf import Form, DecimalField, HiddenInput
from flaskext.wtf import Required, Optional
from flaskext.wtf.html5 import EmailField


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
