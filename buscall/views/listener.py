from buscall import app
from flask import render_template, request, flash, redirect, url_for, abort, g
from ..decorators import login_required
from google.appengine.api import users
from buscall.models.listener import BusListener, BusNotification
from buscall.models.profile import UserProfile
from buscall.forms import BusListenerForm
from buscall.util import GqlQuery, DAYS_OF_WEEK, READONLY_ERR_MSG
import simplejson as json
try:
    from collections import OrderedDict
except ImportError:
    from collections_backport import OrderedDict

@app.route('/listeners')
@login_required
def index_listeners():
    user = users.get_current_user()
    listeners = GqlQuery("SELECT * FROM BusListener WHERE user = :user", user=user) 
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
        if g.readonly:
            flash(READONLY_ERR_MSG, category="error")
            return redirect(url_for("lander"), 303)
        user = users.get_current_user()
        profile = UserProfile.get_by_user(user)
        params = {
            "userprofile": profile,
            "seen": False,
        }
        for param in ('agency_id', 'route_id', 'direction_id', 'stop_id', 'start', 'recur'):
            params[param] = form.data[param]
        # if recur is true, use checkbox table.
        # if recur is false, use dropdown.
        checkboxes = [form.data[day] for day in DAYS_OF_WEEK]
        dropdown = [form.data['dow'] == day for day in DAYS_OF_WEEK]
        if form.data['recur']:
            week_info = checkboxes
        else:
            week_info = dropdown
        for day, value in zip(DAYS_OF_WEEK, week_info):
            params[day] = value

        listener = BusListener(**params)
        listener.put()
        for notification_data in form.data['notifications']:
            notification = BusNotification(listener=listener, minutes=notification_data['minutes'], medium=notification_data['medium'], seen=False)
            notification.put()

        profile.total_listeners_created += 1
        profile.put()

        flash("Alert created!", category="success")
        return redirect(url_for("lander"), 303)
    context = {
        "form": form,
        "js_file": "listeners",
        # "js_model": make_js_model(**kwargs),
        "DAYS_OF_WEEK": DAYS_OF_WEEK,
    }
    return render_template("listeners/new.html", **context)

"""
def make_js_model(agency_id=None, route_id=None, direction_id=None, stop_id=None):
    model = OrderedDict()
    for key, value in AGENCIES.items():
        model[key] = {"title": value.title}
    
    if agency_id in AGENCIES:
        routes = get_routes(agency_id)
        # if we can't access the NextBus API, just return what we have
        if not routes:
            return json.dumps(model)
        route_list = [(id, route_info.title) for id, route_info in routes.iteritems()]
        route_dict = OrderedDict()
        for id, title in route_list:
            route_dict[id] = {"title": title}
        route_dict["_order"] = routes.keys()
        model[agency_id]["routes"] = route_dict

        if route_id in routes:
            route_info = get_route(agency_id, route_id, use_dicts=True)
            directions = route_info.directions
            dir_dict = {}
            for id, dir_info in directions.items():
                dir_dict[id] = dir_info
            model[agency_id]["routes"][route_id]["directions"] = dir_dict

            stops = route_info.stops
            stop_dict = {}
            for id, stop_info in stops.items():
                stop_dict[id] = {"title": stop_info.title}
            stop_dict["_order"] = stop_dict.keys()
            model[agency_id]["routes"][route_id]["stops"] = stop_dict   
    return json.dumps(model)
"""

def get_listener_form_with_defaults(form=None, agency_id=None, route_id=None, direction_id=None, stop_id=None):
    if form is None:
        form = BusListenerForm(request.form)
    """
    if agency_id in AGENCIES:
        # filter out the blank choice
        form.agency_id.choices = [c for c in form.agency_id.choices if c != ('', '')]
        # set the default
        form.agency_id.default = agency_id
        # need to set "data" attribute so that it will render as default
        form.agency_id.data = agency_id
        # pull the routes already: no need for the extra waiting
        routes = get_routes(agency_id)
        # if we can't access the NextBus API, just return the form
        if not routes:
            return form
        route_list = [(id, route_info.title) for id, route_info in routes.iteritems()]
        form.route_id.choices = [('','')] + route_list

        if route_id in routes:
            # filter out the blank choice
            form.route_id.choices = [c for c in form.route_id.choices if c != ('', '')]
            # set the default
            form.route_id.default = route_id
            # need to set "data" attribute so that it will render as default
            form.route_id.data = route_id
            # pull the directions already: no need for the extra waiting
            route_info = get_route(agency_id, route_id, use_dicts=True)
            directions = route_info.directions
            dir_list = [(dir_id, dir_info.title) for dir_id, dir_info in directions.items()]
            form.direction_id.choices = [('','')] + dir_list

            if direction_id in directions:
                # filter out the blank choice
                form.direction_id.choices = [c for c in form.direction_id.choices if c != ('', '')]
                # set the default
                form.direction_id.default = direction_id
                # need to set "data" attribute so that it will render as default
                form.direction_id.data = direction_id
                # pull the stops already: no need for the extra waiting 
                stops = route_info.stops
                stop_list = [(id, stop_info.title) for id, stop_info in stops.items()]
                form.stop_id.choices = [('','')] + stop_list
                
                if stop_id in stops:
                    # filter out the blank choice
                    form.stop_id.choices = [c for c in form.stop_id.choices if c != ('', '')]
                    # set the default
                    form.stop_id.default = stop_id
                    # need to set "data" attribute so that it will render as default
                    form.stop_id.data = stop_id         
    """
    return form

@app.route('/listeners/<int:listener_id>', methods=['DELETE'])
@login_required
def destroy_listener(listener_id):
    userprofile = UserProfile.get_by_user(users.get_current_user())
    listener = BusListener.get_by_id(listener_id)
    if not listener:
        abort(404)
    if listener.userprofile != userprofile:
        abort(401)
    listener.delete()
    flash('Alert deleted!', category="success")
    return redirect(url_for('lander'), 303)
    
