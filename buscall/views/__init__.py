from buscall import app
from flask import render_template, request, flash
from .nextbus import index_routes, show_route, predict_for_stop
from .twilio import call_prediction
from .profile import index_listeners
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
    if request.method == 'POST' and form.validate():
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
        mail.send_mail(sender="Bus Calling <noreply@buscalling.appspotmail.com>",
            to="David Baumgold <singingwolfboy@gmail.com>",
            subject="New waitlist email: " + email,
            body=ALERT_MAIL_BODY % (email, ip, pt.lat, pt.lon))

        # clear form
        form = WaitlistForm()
    return render_template('lander.html', form=form)

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"