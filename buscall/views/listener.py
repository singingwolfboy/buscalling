from buscall import app
from ndb import Key
from flask import render_template, request, flash, redirect, url_for, abort, g
from ..decorators import login_required
from google.appengine.api import users
from buscall.models.listener import BusListener, ScheduledNotification
from buscall.models.profile import UserProfile
from buscall.models.nextbus import Agency, Route, Direction, Stop
from buscall.forms import BusListenerForm
from buscall.util import DAYS_OF_WEEK, READONLY_ERR_MSG

@app.route('/listeners')
@login_required
def index_listeners():
    user = users.get_current_user()
    profile_key = Key(UserProfile, user.user_id())
    listeners = BusListener.query(BusListener.profile_key == profile_key)
    return render_template('listeners/index.html', listeners=listeners)

@app.route('/listeners/new', methods=['GET', 'POST'])
@login_required
def new_listener(agency_id="mbta", route_id=None, direction_id=None, stop_id=None):
    """
    kwargs = {
        "agency_id":    agency_id    or request.args.get('agency', None),
        "route_id":     route_id     or request.args.get('route', None),
        "direction_id": direction_id or request.args.get('direction', None),
        "stop_id":      stop_id      or request.args.get('stop', None),
    }
    """
    agencies = Agency.query()
    form = BusListenerForm(request.form)
    if form.validate_on_submit():
        user = users.get_current_user()
        profile_key =Key(UserProfile, user.user_id())
        params = {
            "profile_key": profile_key,
            "agency_key": Key(Agency, form.data["agency_id"]),
            "route_key": Key(Route, "{agency_id}|{route_id}".format(**form.data)),
            "direction_key": Key(Direction, "{agency_id}|{route_id}|{direction_id}".format(**form.data)),
            "stop_key": Key(Stop, "{agency_id}|{route_id}|{direction_id}|{stop_id}".format(**form.data)),
            "start": form.data["start"],
            "recur": form.data["recur"],

        }
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
        notifications = []
        for notification_data in form.data['notifications']:
            notifications.append(ScheduledNotification(
                    minutes_before=notification_data['minutes'],
                    medium=notification_data['medium'],
                    has_executed=False))
        listener.scheduled_notifications = notifications
        listener.put()

        profile = profile_key.get()
        profile.total_listeners_created += 1
        profile.put()

        flash("Alert created!", category="success")
        return redirect(url_for("lander"), 303)
    context = {
        "form": form,
        "js_file": "listeners",
        "agencies": agencies,
        "DAYS_OF_WEEK": DAYS_OF_WEEK,
    }
    return render_template("listeners/new.html", **context)

@app.route('/listeners/<int:listener_id>', methods=['DELETE'])
@login_required
def destroy_listener(listener_id):
    user = users.get_current_user()
    profile_key = Key(UserProfile, user.user_id())
    listener = BusListener.get_by_id(listener_id)
    if not listener:
        abort(404)
    if listener.profile_key != profile_key:
        abort(401)
    listener.key.delete()
    flash('Alert deleted!', category="success")
    return redirect(url_for('lander'), 303)
    
