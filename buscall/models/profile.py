from google.appengine.api import users
from google.appengine.ext import db

class UserProfile(db.Model):
    user = db.UserProperty(required=True)
    paid = db.BooleanProperty(required=True, default=False)
    joined = db.DateTimeProperty(required=True, auto_now_add=True)
    last_login = db.DateTimeProperty(required=True, auto_now=True)

    # optional properties
    phone = db.PhoneNumberProperty()
    first_name = db.StringProperty()
    last_name = db.StringProperty()

    # pass-throughs
    @property
    def email(self):
        return self.user.email()
    @property
    def nickname(self):
        return self.user.nickname()
    @property
    def user_id(self):
        return self.user.user_id()
    @property
    def federated_identity(self):
        return self.user.federated_identity()
    @property
    def federated_provider(self):
        return self.user.federated_provider()
    
    # set key_name to user's ID or email address
    def __init__(self, *args, **kwargs):
        if not 'key' in kwargs and not 'key_name' in kwargs:
            kwargs['key_name'] = kwargs['user'].user_id() or kwargs['user'].email()
        db.Model.__init__(self, *args, **kwargs)