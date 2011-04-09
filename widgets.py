from wtforms import fields, widgets
from wtforms.ext.appengine import db
import logging

class GeoPtHiddenInput(widgets.HiddenInput):
    def __init__(self, *args, **kwargs):
        super(GeoPtHiddenInput, self).__init__(*args, **kwargs)
    
    def _value(self):
        return self.data

    def __call__(self, field, **kwargs):
        kwargs.setdefault('type', 'hidden')
        field_id = kwargs.pop('id', field.id)
        lat_value, long_value = kwargs.pop('value', field._value())
        html = u'<input %s /><input %s />' % (
            widgets.html_params(id=field_id+"_lat", value=lat_value, **kwargs),
            widgets.html_params(id=field_id+"_long", value=long_value, **kwargs))
        return widgets.HTMLString(html)

class GeoPtPropertyField(fields.TextField):
    widget = GeoPtHiddenInput()
    default = (u'', u'')

    def __init__(self, default=(u'', u''), **kwargs):
        super(GeoPtPropertyField, self).__init__(default=default, **kwargs)
    
    def _value(self):
        return self.data or (u'', u'')

    def process_formdata(self, valuelist):
        if valuelist:
            logging.warning("valuelist: ", valuelist)
        else:
            logging.warning("NO VALUELIST")

def convert_GeoPtProperty(model, prop, kwargs):
    return GeoPtPropertyField(**kwargs)

class ModelConverter(db.ModelConverter):
    def __init__(self, converters=None):
        super(ModelConverter, self).__init__(converters)
        self.converters['GeoPtProperty'] =convert_GeoPtProperty