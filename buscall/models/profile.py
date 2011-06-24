from google.appengine.api import users
from google.appengine.ext import db

class UserProfile(db.Model):
    user = db.UserProperty(required=True)
    phone = db.PhoneNumberProperty()