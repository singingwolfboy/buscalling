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
    def name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
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

    @classmethod
    def get_by_user(cls, user):
        key_name = user.user_id() or user.email()
        return cls.get_by_key_name(key_name)
    
    @classmethod
    def get_or_insert_by_user(cls, user):
        key_name = user.user_id() or user.email()
        return cls.get_or_insert(key_name, user=user)