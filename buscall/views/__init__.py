from buscall import app
from flask import render_template, request, flash, redirect, url_for
from .tasks import poll, reset_seen_flags
from .nextbus import show_agency, routes_for_agency, show_route, predict_for_stop
from .twilio import call_prediction
from .listener import index_listeners, new_listener
from .paypal import paypal_ipn
from .profile import update_profile
from buscall.util import MAIL_SENDER, GqlQuery
from buscall.models import WaitlistEntry, BusListener, UserProfile
from buscall.models.paypal import url as paypal_url
from buscall.models.paypal import subscribe_button_id, unsubscribe_button_id
from buscall.forms import WaitlistForm, UserProfileForm
from google.appengine.api import memcache, mail
from google.appengine.ext import db
from google.appengine.api import users
import datetime

ALERT_MAIL_BODY = """
Someone signed up for the Bus Calling waitlist!
email: %s
ip: %s
location: %s, %s
""".strip()

@app.context_processor
def inject_profile():
    profile = UserProfile.get_current_profile()
    return {
        "profile": profile,
        "profile_form": UserProfileForm(request.form, profile),
    }

@app.before_request
def inject_auth_urls():
    app.add_url_rule(users.create_login_url(request.url),        "login")
    app.add_url_rule(users.create_logout_url(url_for('lander')), "logout")

@app.before_request
def update_userprofile_last_login():
    profile = UserProfile.get_current_profile()
    if profile:
        profile.last_access = datetime.datetime.now()
        db.put_async(profile)

@app.template_filter('timeformat')
def time_format(time):
    s = time.strftime("%I:%M%p")
    if s.startswith("0"):
        s = s[1:]
    return s

@app.route('/')
def page_root():
    user = users.get_current_user()
    if user:
        args = dict(
            profile = UserProfile.get_or_insert_by_user(user),
            paypay_url = paypal_url,
            sub_id = subscribe_button_id,
            unsub_id = unsubscribe_button_id,
        )
        return render_template("dashboard.html", **args)
    else:
        return render_template('lander.html')
app.add_url_rule('/', 'dashboard', page_root)
app.add_url_rule('/', 'lander', page_root)
