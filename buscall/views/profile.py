from buscall import app
from flask import render_template, request, flash, redirect, url_for
from ..decorators import login_required
from google.appengine.api import users
from buscall.models.profile import BusListener
from buscall.forms import BusListenerForm
from google.appengine.ext.db import GqlQuery as TruthyGqlQuery
from buscall.models.nextbus import AGENCIES, get_routes
import simplejson as json

class GqlQuery(TruthyGqlQuery):
    def __nonzero__(self):
        return self.count(1) != 0

@app.route('/listeners')
@login_required
def index_listeners():
    listeners = GqlQuery("SELECT * FROM BusListener WHERE user = :1", 
        users.get_current_user())
    return render_template('listeners/index.html', listeners=listeners)

@app.route('/listeners/new', methods=['GET', 'POST'])
@login_required
def new_listener(agency_id="mbta"):
    form = BusListenerForm()
    js_model = {}
    for key, value in AGENCIES.items():
        js_model[key] = {"name": value}
    # set default agency
    if agency_id and agency_id in AGENCIES:
        # filter out the blank choice
        form.agency_id.choices = [c for c in form.agency_id.choices if c != ('', '')]
        # set the default
        form.agency_id.default = agency_id
        # need to set "data" attribute so that it will render as default
        form.agency_id.data = agency_id
        # pull the routes already: no need for the extra waiting
        routes = [(r['id'], r['title']) for r in get_routes(agency_id) ]
        form.route_id.choices = [('','')] + routes
        # include this info in the JS model
        js_model[agency_id]["routes"] = routes
    if form.validate_on_submit():
        user = users.get_current_user()
        listener = BusListener(user=user)
        for param in ('route_id', 'stop_id', 'start', 'end', \
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'):
            setattr(listener, param, form.data[param])
        listener.put()
        flash("Listener created!")
        return redirect(url_for("index_listeners"))
    return render_template("listeners/new.html", form=form, 
        js_file="listeners", js_model=json.dumps(js_model))

