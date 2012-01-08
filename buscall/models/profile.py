from google.appengine.api import users
from ndb import model, Key
from buscall.models.listener import BusListener

class UserProfile(model.Model):
    user_id = model.StringProperty(required=True)

    # reporting/historical
    joined = model.DateTimeProperty(required=True, auto_now_add=True)
    last_access = model.DateTimeProperty(required=True, auto_now=True)
    total_listeners_created = model.IntegerProperty(default=0)

    # money-related properties
    # freeloader starts as True, becomes False as soon as they spend any money at all
    freeloader = model.BooleanProperty(default=True)
    # whether the user is currently a paid subscriber
    subscribed = model.BooleanProperty(default=False)
    # one-off pickup credits (new users get 5 as a free trial)
    credits = model.IntegerProperty(default=5)

    # optional properties
    phone = model.StringProperty()
    first_name = model.StringProperty()
    last_name = model.StringProperty()

    @property
    def user(self):
        return users.User(self.user_id)

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
    def federated_identity(self):
        return self.user.federated_identity()
    @property
    def federated_provider(self):
        return self.user.federated_provider()

    @property
    def listeners(self):
        return BusListener.query(BusListener.profile_key == self.key)

    def __cmp__(self, othr):
        if not isinstance(othr, UserProfile):
            return NotImplemented
        # we won't compare last_access, since that always changes
        return cmp((self.user_id, self.subscribed, self.credits, self.joined, self.phone, self.first_name, self.last_name),
                   (othr.user_id, othr.subscribed, othr.credits, othr.joined, othr.phone, othr.first_name, othr.last_name))

    def phone_required(self):
        for listener in self.listeners:
            for notification in listener.scheduled_notifications:
                if notification.medium in ['phone', 'txt']:
                    return True
        return False

    @classmethod
    def get_by_user(cls, user):
        key = Key(UserProfile, user.user_id())
        return key.get()

    @classmethod
    def get_current_profile(cls):
        user = users.get_current_user()
        if user:
            return cls.get_by_user(user)
        return None

