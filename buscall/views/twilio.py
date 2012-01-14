from __future__ import absolute_import

from buscall import app
from ndb import Key
from twilio_api import Account, HTTPErrorAppEngine
import simplejson as json
from google.appengine.api import users
from buscall.models.nextbus import Route, Stop, BusPrediction
from buscall.decorators import admin_required
from buscall.credentials import ACCOUNT_SID, ACCOUNT_TOKEN, PHONE_NUMBER
from buscall.util import DOMAIN, pluralize_minutes
from flask import url_for

API_VERSION = "2010-04-01"
account = Account(ACCOUNT_SID, ACCOUNT_TOKEN)

@app.route("/call/<agency_id>/<route_id>/<direction_id>/<stop_id>/<phone_num>")
@app.route("/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/call/<phone_num>")
@admin_required
def call_prediction(agency_id, route_id, direction_id, stop_id, phone_num):
    user = users.get_current_user()
    app.logger.info("%s (%s) called %s" % (user.nickname(), user.user_id(), phone_num))
    url = DOMAIN + url_for('prediction_list', agency_id=agency_id,
        route_id=route_id, direction_id=direction_id, stop_id=stop_id, format="twiml")
    call_info = {
        'From': PHONE_NUMBER,
        'To': phone_num,
        'Url': url,
        'Method': 'GET',
    }
    try:
        call_json = account.request(
            '/%s/Accounts/%s/Calls.json' % (API_VERSION, ACCOUNT_SID),
            'POST', 
            call_info)
        app.logger.info(call_json)
        call = json.loads(call_json)
        return "Now calling %s with call ID %s" % (call['to'], call['sid'])
    except HTTPErrorAppEngine, e:
        app.logger.error(e)
        try:
            err = json.loads(e.msg)
            message = err['Message']
            return "REMOTE ERROR: %s" % (message,)
        except:
            return "Couldn't parse error output:<br>\n%s" % e.msg

@app.route("/sms/<agency_id>/<route_id>/<direction_id>/<stop_id>/<phone_num>")
@app.route("/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/sms/<phone_num>")
@admin_required
def sms_prediction(agency_id, route_id, direction_id, stop_id, phone_num):
    user = users.get_current_user()
    app.logger.info("%s (%s) texted %s" % (user.nickname(), user.user_id(), phone_num))
    predictions = BusPrediction.query(
            agency_id=agency_id,
            route_id=route_id,
            direction_id=direction_id,
            stop_id=stop_id)
    route = Key(Route, route_id).get()
    if route:
        route_name = route.name
    else:
        route_name = "<unknown route>"
    stop = Key(Stop, stop_id).get()
    if stop:
        stop_name = stop.name
    else:
        stop_name = "<unknown stop>"
    if len(predictions) > 1:
        first = predictions[0]
        rest = predictions[1:]
        body = "%s until %s arrives at %s. %d more buses: %s." % (
            pluralize_minutes(first.minutes),
            route_name,
            stop_name,
            len(rest),
            ", ".join([pluralize_minutes(bus.minutes) for bus in rest]),
        )
    elif len(predictions) == 1:
        first = predictions[0]
        next = predictions[1]
        body = "%s until %s arrives at %s. One more bus in %s." % (
            pluralize_minutes(first.minutes),
            route_name,
            stop_name,
            pluralize_minutes(next.minutes),
        )
    else:
        body = "No buses predicted (%s, %s)" % (route.name, stop.name)

    sms_info = {
        'From': PHONE_NUMBER,
        'To': phone_num,
        'Body': body,
    }
    sms = json.loads(account.request(
        '/%s/Accounts/%s/SMS/Messages.json' % (API_VERSION, ACCOUNT_SID),
        'POST',
        sms_info,
    ))
    return "Now texting %s with sms ID %s" % (sms['to'], sms['sid'])
