from google.appengine.api import users
from google.appengine.ext import db
from buscall.models.profile import UserProfile
from buscall.util import CurrencyProperty

class Transaction(db.Model):
    processor = db.StringProperty(required=True, choices=['paypal', 'amazon'])
    id = db.StringProperty(required=True)
    userprofile = db.ReferenceProperty(UserProfile, required=True, collection_name="transactions")
    date = db.DateTimeProperty(required=True)
    amount = CurrencyProperty(required=True)
    subscription_id = db.StringProperty()
    payment_status = db.StringProperty()
