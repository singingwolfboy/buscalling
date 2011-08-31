from google.appengine.api import users
from google.appengine.ext import db
from collections import defaultdict
from buscall.util import GqlQuery

class UserProfile(db.Expando):
    user = db.UserProperty(required=True)
    joined = db.DateTimeProperty(required=True, auto_now_add=True)
    last_access = db.DateTimeProperty(required=True, auto_now=True)

    # money-related properties
    # freeloader starts as True, becomes False as soon as they spend any money at all
    freeloader = db.BooleanProperty(required=True, default=True)
    # whether the user is currently a paid subscriber
    subscribed = db.BooleanProperty(required=True, default=False)
    # one-off alert credits (new users get 10 as a free trial)
    credits = db.IntegerProperty(required=True, default=10)

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

    def __cmp__(self, othr):
        if not isinstance(othr, UserProfile):
            return NotImplemented
        # we won't compare last_access, since that always changes
        return cmp((self.user, self.subscribed, self.credits, self.joined, self.phone, self.first_name, self.last_name),
                   (othr.user, othr.subscribed, othr.credits, othr.joined, othr.phone, othr.first_name, othr.last_name))

    @classmethod
    def get_by_user(cls, user):
        key_name = user.user_id() or user.email()
        return cls.get_by_key_name(key_name)
    
    @classmethod
    def get_or_insert_by_user(cls, user):
        key_name = user.user_id() or user.email()
        return cls.get_or_insert(key_name, user=user)