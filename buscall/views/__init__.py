from buscall import app
from flask import render_template, request, flash
from .nextbus import index_routes, show_route, predict_for_stop
from .twilio import call_prediction
from buscall.models import WaitlistEntry
from buscall.forms import WaitlistForm
from google.appengine.api import memcache
from google.appengine.ext import db

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

        entry = WaitlistEntry(email=form.email.data, ip=ip, location=pt)
        entry.put()
        flash("Thanks, %s! You're on the waitlist." % (form.email.data,))
        # clear form
        form = WaitlistForm()
    return render_template('lander.html', form=form)

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"