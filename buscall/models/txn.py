from ndb import model
from buscall.util import DecimalProperty

class Subscription(model.Model):
    user_key = model.KeyProperty(required=True)
    processor = model.StringProperty(required=True, choices=['paypal', 'amazon'])
    subscription_id = model.StringProperty(required=True)
    active = model.BooleanProperty(default=True)
    start_track_id = model.StringProperty()
    end_track_id = model.StringProperty()
    start_date = model.DateTimeProperty(required=True)
    end_date = model.DateTimeProperty()
    amount = DecimalProperty(required=True)

class Payment(model.Model):
    processor = model.StringProperty(required=True, choices=['paypal', 'amazon'])
    subscription_key = model.KeyProperty()
    transaction_id = model.StringProperty(required=True)
    date = model.DateTimeProperty(required=True)
    amount = DecimalProperty(required=True)
    status = model.StringProperty(required=True)
    track_id = model.StringProperty()
    item_id = model.IntegerProperty()
    quantity = model.IntegerProperty()  # the default is NOT 1, it is None, aka unknown
