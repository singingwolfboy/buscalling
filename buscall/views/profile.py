from buscall import app
from flask import render_template, request, flash, redirect, url_for
from ..decorators import login_required
from google.appengine.api import users
from buscall.models.profile import BusListener
from buscall.forms import BusListenerForm
from google.appengine.ext.db import GqlQuery as TruthyGqlQuery
from buscall.models.nextbus import AGENCIES, get_routes, get_route
from buscall.models.profile import days_of_week
import simplejson as json
try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

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
def new_listener(agency_id="mbta", route_id=None, direction_id=None, stop_id=None):
    kwargs = {
        "agency_id":    agency_id    or request.args.get('agency', None),
        "route_id":     route_id     or request.args.get('route', None),
        "direction_id": direction_id or request.args.get('direction', None),
        "stop_id":      stop_id      or request.args.get('stop', None),
    }
    form = get_listener_form_with_defaults(BusListenerForm(request.form), **kwargs)
    if form.validate_on_submit():
        user = users.get_current_user()
        listener = BusListener(user=user)
        for param in ('route_id', 'stop_id', 'start', 'end', \
            'mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'):
            setattr(listener, param, form.data[param])
        listener.put()
        flash("Listener created!")
        return redirect(url_for("index_listeners"))
    context = {
        "form": form,
        "js_file": "listeners",
        "js_model": make_js_model(**kwargs),
        "days_of_week": days_of_week,
    }
    return render_template("listeners/new.html", **context)

def make_js_model(agency_id=None, route_id=None, direction_id=None, stop_id=None):
    model = OrderedDict()
    for key, value in AGENCIES.items():
        model[key] = {"name": value}
    
    if agency_id in AGENCIES:
        routes = get_routes(agency_id)
        route_list = [(id, route_info['title']) for id, route_info in routes.iteritems()]
        route_dict = OrderedDict()
        for id, title in route_list:
            route_dict[id] = {"title": title}
        route_dict["_order"] = routes.keys()
        model[agency_id]["routes"] = route_dict

        if route_id in routes:
            route_info = get_route(agency_id, route_id)
            directions = route_info['directions']
            dir_dict = {}
            for id, dir_info in directions.items():
                del dir_info["useForUI"]
                dir_dict[id] = dir_info
            model[agency_id]["routes"][route_id]["directions"] = dir_dict

            stops = route_info['stops']
            stop_dict = {}
            for id, stop_info in stops.items():
                stop_dict[id] = {"title": stop_info["title"]}
            stop_dict["_order"] = stop_dict.keys()
            model[agency_id]["routes"][route_id]["stops"] = stop_dict   
    return json.dumps(model)

def get_listener_form_with_defaults(form=None, agency_id=None, route_id=None, direction_id=None, stop_id=None):
    if form is None:
        form = BusListenerForm(request.form)
    if agency_id in AGENCIES:
        # filter out the blank choice
        form.agency_id.choices = [c for c in form.agency_id.choices if c != ('', '')]
        # set the default
        form.agency_id.default = agency_id
        # need to set "data" attribute so that it will render as default
        form.agency_id.data = agency_id
        # pull the routes already: no need for the extra waiting
        routes = get_routes(agency_id)
        route_list = [(id, route_info['title']) for id, route_info in routes.iteritems()]
        form.route_id.choices = [('','')] + route_list

        if route_id in routes:
            # filter out the blank choice
            form.route_id.choices = [c for c in form.route_id.choices if c != ('', '')]
            # set the default
            form.route_id.default = route_id
            # need to set "data" attribute so that it will render as default
            form.route_id.data = route_id
            # pull the directions already: no need for the extra waiting
            route_info = get_route(agency_id, route_id)
            directions = route_info['directions']
            dir_list = [(dir_id, dir_info['title']) for dir_id, dir_info in directions.items()]
            form.direction_id.choices = [('','')] + dir_list

            if direction_id in directions:
                # filter out the blank choice
                form.direction_id.choices = [c for c in form.direction_id.choices if c != ('', '')]
                # set the default
                form.direction_id.default = direction_id
                # need to set "data" attribute so that it will render as default
                form.direction_id.data = direction_id
                # pull the stops already: no need for the extra waiting 
                stops = route_info['stops']
                stop_list = [(id, stop_info['title']) for id, stop_info in stops.items()]
                form.stop_id.choices = [('','')] + stop_list
                
                if stop_id in stops:
                    # filter out the blank choice
                    form.stop_id.choices = [c for c in form.stop_id.choices if c != ('', '')]
                    # set the default
                    form.stop_id.default = stop_id
                    # need to set "data" attribute so that it will render as default
                    form.stop_id.data = stop_id         
    return form
