from google.appengine.api import users
from google.appengine.ext import db
from buscall.models.profile import UserProfile
from buscall.util import CurrencyProperty

class Transaction(db.Model):
    # parent should be the UserProfile of the user who made the transaction
    processor = db.StringProperty(required=True, choices=['paypal', 'amazon'])
    id = db.StringProperty(required=True)
    date = db.DateTimeProperty(required=True)
    amount = CurrencyProperty(required=True)
    subscription_id = db.StringProperty()
    payment_status = db.StringProperty()
