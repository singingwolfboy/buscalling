from buscall import app
from flask import render_template, request, flash, redirect, url_for
from .nextbus import show_agency, routes_for_agency, show_route, predict_for_stop
from .twilio import call_prediction
from .listener import index_listeners
from buscall.util import MAIL_SENDER, GqlQuery
from buscall.models import WaitlistEntry, BusListener
from buscall.forms import WaitlistForm
from google.appengine.api import memcache, mail
from google.appengine.ext import db
from google.appengine.api import users

ALERT_MAIL_BODY = """
Someone signed up for the Bus Calling waitlist!
email: %s
ip: %s
location: %s, %s
""".strip()

@app.context_processor
def inject_user():
    return dict(user=users.get_current_user())

@app.before_request
def add_auth_url_rules():
    app.add_url_rule(users.create_login_url( request.url), 'login')
    app.add_url_rule(users.create_logout_url(url_for('lander')), 'logout')

@app.route('/', methods = ['GET', 'POST'])
def lander():
    user = users.get_current_user()
    if user:
        return lander_user()
    else:
        return lander_guest()

def lander_guest():
    form = WaitlistForm(request.form)
    if form.validate_on_submit():
        try:
            ip = request.environ['HTTP_X_FORWARDED_FOR']
        except KeyError:
            try:
                ip = request.environ['REMOTE_ADDR']
            except KeyError:
                ip = None
        
        if request.form['location_lat'] and request.form['location_long']:
            pt = db.GeoPt(request.form['location_lat'], request.form['location_long'])
        else:
            pt = None

        email = form.email.data
        entry = WaitlistEntry(email=email, ip=ip, location=pt)
        entry.put()
        flash("Thanks, %s! You're on the waitlist." % (email,))

        # alert via mail
        try:
            lat = pt.lat
            lon = pt.lon
        except AttributeError:
            lat = None
            lon = None
        mail.send_mail(sender=MAIL_SENDER,
            to="David Baumgold <singingwolfboy@gmail.com>",
            subject="New waitlist email: " + email,
            body=ALERT_MAIL_BODY % (email, ip, lat, lon))

        return redirect(url_for("lander"))
    return render_template('lander_guest.html', form=form, js_file="lander")

def lander_user():
    user = users.get_current_user()
    listeners = GqlQuery("SELECT * FROM BusListener WHERE user = :user", user=user)
    return render_template("lander_user.html", user=user, listeners=listeners)
