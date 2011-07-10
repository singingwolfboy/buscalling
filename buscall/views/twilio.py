from __future__ import absolute_import

from buscall import app
from twilio_api import Account, HTTPErrorAppEngine
import simplejson as json
from google.appengine.api import users
from buscall.decorators import login_required
from buscall.credentials import ACCOUNT_SID, ACCOUNT_TOKEN, PHONE_NUMBER
from buscall.util import DOMAIN
from flask import url_for

API_VERSION = "2010-04-01"
account = Account(ACCOUNT_SID, ACCOUNT_TOKEN)

@app.route("/call/<agency_id>/<route_id>/<direction_id>/<stop_id>/<phone_num>")
@app.route("/<agency_id>/routes/<route_id>/directions/<direction_id>/stops/<stop_id>/call/<phone_num>")
def call_prediction(agency_id, route_id, direction_id, stop_id, phone_num):
	user = users.get_current_user()
	if not user:
		return redirect(url_for('login'))
	app.logger.info("%s (%s) called %s" % (user.nickname(), user.user_id(), phone_num))
	url = DOMAIN + url_for('predict_for_stop', agency_id=agency_id, 
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

