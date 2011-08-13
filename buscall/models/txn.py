from google.appengine.api import users
from google.appengine.ext import db
from buscall.models.profile import UserProfile
from buscall.util import CurrencyProperty

class Subscription(db.Model):
    userprofile = db.ReferenceProperty(UserProfile, required=True, collection_name="transactions")
    processor = db.StringProperty(required=True, choices=['paypal', 'amazon'])
    subscription_id = db.StringProperty(required=True)
    active = db.BooleanProperty(required=True, default=True)
    start_track_id = db.StringProperty()
    end_track_id = db.StringProperty()
    start_date = db.DateTimeProperty(required=True)
    end_date = db.DateTimeProperty()
    amount = CurrencyProperty(required=True)

class Payment(db.Model):
    processor = db.StringProperty(required=True, choices=['paypal', 'amazon'])
    subscription = db.ReferenceProperty(Subscription, collection_name="payments")
    transaction_id = db.StringProperty(required=True)
    date = db.DateTimeProperty(required=True)
    amount = CurrencyProperty(required=True)
    status = db.StringProperty(required=True)
    track_id = db.StringProperty()
