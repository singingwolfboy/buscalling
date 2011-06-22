from buscall import app
from flask import render_template, request, flash, redirect, url_for
from .nextbus import show_agency, routes_for_agency, show_route, predict_for_stop
try:
    from .twilio import call_prediction
except AttributeError:
    print("Could not import Twilio call_prediction view: ignoring.")
from .listener import index_listeners
from buscall.models import WaitlistEntry
from buscall.forms import WaitlistForm
from google.appengine.api import memcache, mail
from google.appengine.ext import db

ALERT_MAIL_BODY = """
Someone signed up for the Bus Calling waitlist!
email: %s
ip: %s
location: %s, %s
""".strip()

@app.route('/', methods = ['GET', 'POST'])
def lander():
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
        mail.send_mail(sender="Bus Calling <noreply@buscalling.appspotmail.com>",
            to="David Baumgold <singingwolfboy@gmail.com>",
            subject="New waitlist email: " + email,
            body=ALERT_MAIL_BODY % (email, ip, lat, lon))

        return redirect(url_for("lander"))
    return render_template('lander.html', form=form, js_file="lander")

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"
