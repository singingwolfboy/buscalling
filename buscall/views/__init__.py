from buscall import app
from ndb import Key
from flask import render_template, request, flash, redirect, url_for, g, abort
from .tasks import poll, reset_seen_flags
from .nextbus import *
from .twilio import call_prediction
from .listener import index_listeners, new_listener
from .paypal import paypal_ipn
from .user import update_user
from .util import ExtJSONEncoder
from buscall.util import READONLY_ERR_MSG, get_request_format
from buscall.models import User
from buscall.models.paypal import url as paypal_url, button_id as paypal_button_id
from buscall.models.listener import NOTIFICATION_CHOICES
from buscall.forms import UserForm
from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api.capabilities import CapabilitySet
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
import os
import datetime
import simplejson as json
from jinja2.tests import test_defined
from markupsafe import Markup

@app.context_processor
def inject_base_vars():
    user = User.get_current_user()
    return {
        "user": user,
        "user_form": UserForm(request.form, user),
        "paypal_url": paypal_url,
        "paypal_button_id": paypal_button_id,
        "medium_map": dict(NOTIFICATION_CHOICES),
    }

@app.context_processor
def inject_env():
    return {"env": os.environ}

@app.context_processor
def inject_auth_urls():
    login_url  = users.create_login_url(request.url)
    logout_url = users.create_logout_url(url_for('lander'))

    # It would be nice if we could hook these URLs up to the 
    # Flask routing system, like so:
    #
    # (change @app.context_processor to @app.before_request)
    # app.add_url_rule(login_url,  "login",  build_only=True)
    # app.add_url_rule(logout_url, "logout", build_only=True)
    #
    # Unfortunately, in production those URLs are on a different domain,
    # and the Flask routing system can't handle URLs to arbitrary domains. 
    # So instead, we'll use a context processor to provide the URLs to 
    # the template as variables.

    return dict(login_url=login_url, logout_url=logout_url)

@app.before_request
def update_user_last_access():
    user = User.get_current_user()
    if user:
        user.last_access = datetime.datetime.utcnow()
        user.put_async()

@app.before_request
def set_request_format():
    g.request_format = get_request_format()

@app.template_filter('timeformat')
def time_format(time):
    return time.strftime("%-I:%M%p")

@app.template_filter('url_dict')
def url_dict(obj):
    if not test_defined(obj):
        return None
    if hasattr(obj, "_as_url_dict"):
        return obj._as_url_dict()
    else:
        return [o._as_url_dict() for o in obj]

@app.template_filter('json')
def to_json(obj):
    if test_defined(obj):
        return Markup(json.dumps(obj, use_decimal=True, cls=ExtJSONEncoder))
    return Markup("null")

@app.route('/')
def page_root():
    google_user = users.get_current_user()
    if google_user:
        user = User.get_from_google_user(google_user)
        if not user:
            # this user's first login
            try:
                user = User.create_from_google_user(google_user)
                user.put()
                # Flash a welcome message, and redirect to new listener form
                flash("Welcome! To set up your first bus alert, just fill out this form.")
            except CapabilityDisabledError:
                flash(READONLY_ERR_MSG, category="warn")
            return redirect(url_for("new_listener"), 303)
        else:
            # If the user has listeners with notifications that rely on a phone number,
            # but they have not entered their phone number, we should warn them of this.
            if not user.phone and user.phone_required():
                flash("At least one of your alerts is set up to notify you "
                    "via phone or text message, but you have not set up your "
                    "phone number yet. To do so, click on \"Edit Profile\" above.",
                    category="warn")
            return render_template("dashboard.html")

    else:
        return render_template('lander.html')
app.add_url_rule('/', 'dashboard', page_root)
app.add_url_rule('/', 'lander', page_root)

@app.route('/flush_all')
def flush_all():
    if not app.debug:
        abort(404)
    if memcache.flush_all():
        return "Flushed"
    else:
        return "Failed"

