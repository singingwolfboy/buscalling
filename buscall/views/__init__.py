from buscall import app
from flask import render_template, request, flash, redirect, url_for, g, abort
from .tasks import poll, reset_seen_flags
from .nextbus import show_agency, routes_for_agency, show_route, predict_for_stop
from .twilio import call_prediction
from .listener import index_listeners, new_listener
from .paypal import paypal_ipn
from .profile import update_profile
from buscall.util import MAIL_SENDER, READONLY_ERR_MSG, GqlQuery, get_request_format
from buscall.models import WaitlistEntry, BusListener, UserProfile
from buscall.models.paypal import url as paypal_url, button_id as paypal_button_id
from buscall.models.listener import NOTIFICATION_CHOICES
from buscall.models.nextbus import get_agencies
from buscall.forms import WaitlistForm, UserProfileForm
from google.appengine.api import memcache, mail
from google.appengine.ext import db
from google.appengine.api import users
from google.appengine.api.capabilities import CapabilitySet
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
import os
import datetime

@app.context_processor
def inject_base_vars():
    profile = UserProfile.get_current_profile()
    return {
        "profile": profile,
        "profile_form": UserProfileForm(request.form, profile),
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
def update_userprofile_last_login():
    g.readonly = CapabilitySet('datastore_v3', capabilities=['write']).is_enabled()
    if not g.readonly:
        profile = UserProfile.get_current_profile()
        if profile:
            profile.last_access = datetime.datetime.now()
            db.put_async(profile)

@app.before_request
def set_request_format():
    g.request_format = get_request_format()

@app.before_request
def pagination():
    try:
        limit = int(request.args.get('limit', 20))
    except ValueError:
        limit = 20
    if limit > 100:
        limit = 100
    if limit < 0:
        limit = 0
    g.limit = limit

    try:
        offset = int(request.args.get('offset', 0))
    except ValueError:
        offset = 0
    if offset < 0:
        offset = 0
    g.offset = offset

@app.before_request
def set_agencies():
    g.AGENCIES = get_agencies()

@app.template_filter('timeformat')
def time_format(time):
    return time.strftime("%-I:%M%p")

@app.route('/')
def page_root():
    user = users.get_current_user()
    if user:
        profile = UserProfile.get_by_user(user)
        if not profile:
            # this user's first login
            try:
                profile = UserProfile.get_or_insert_by_user(user)
                # Flash a welcome message, and redirect to new listener form
                flash("Welcome! To set up your first bus alert, just fill out this form.")
            except CapabilityDisabledError:
                flash(READONLY_ERR_MSG, category="warn")
            return redirect(url_for("new_listener"), 303)
        else:
            # If the user has listeners with notifications that rely on a phone number,
            # but they have not entered their phone number, we should warn them of this.
            if not profile.phone and profile.phone_required():
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
