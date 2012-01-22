from google.appengine.api import users
from ndb import model
from flask import url_for
from buscall.models.listener import BusListener
from .util import resource_uri, template_id

class User(model.Model):
    google_id = model.StringProperty()
    primary_email = model.StringProperty(required=True)

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
    def id(self):
        return self.key.id()

    @property
    def url(self):
        return url_for("user_show", user_id=self.id)

    @property
    def google_user(self):
        if self.google_id:
            return users.User(self.google_id)
        return None

    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return "%s %s" % (self.first_name, self.last_name)
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        else:
            return self.primary_email

    @property
    def listeners(self):
        return BusListener.query(BusListener.user_key == self.key)

    def phone_required(self):
        for listener in self.listeners:
            for notification in listener.scheduled_notifications:
                if notification.medium in ['phone', 'txt']:
                    return True
        return False

    @classmethod
    def get_from_google_user(cls, user):
        return User.query(User.google_id == user.user_id()).get()

    @classmethod
    def get_from_email(cls, email):
        return User.query(User.primary_email == email).get()

    @classmethod
    def create_from_google_user(cls, user):
        return cls(
            google_id = user.user_id(),
            primary_email = user.email(),
        )

    @classmethod
    def create_from_email(cls, email):
        return cls(primary_email=email)

    @classmethod
    def get_current_user(cls):
        user = users.get_current_user()
        if user:
            return cls.get_from_google_user(user)
        return None

    def matches_current_google_user(self):
        if not self.google_id:
            return None
        google_user = users.get_current_user()
        if not google_user:
            return False
        return google_user.user_id() == self.google_id

    def _as_url_dict(self):
        public = ("primary_email", "joined")
        private = ("google_id", "last_access", "subscribed", "credits",
                "first_name", "last_name", "phone")
        if self.matches_current_google_user():
            include = public + private
        else:
            include = public
        d = self._to_dict(include=include)
        d['id'] = self.id
        d[resource_uri] = self.url
        detail_uri_template = url_for('listener_detail', listener_id=12345).replace("12345", template_id)
        d['listeners'] = dict(
            list_uri = url_for('listeners_for_user', user_id=self.id),
            detail_uri_template = detail_uri_template,
            ids = [listener.id for listener in self.listeners],
        )
        return d

