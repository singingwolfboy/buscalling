from buscall import app
import twilio_api as tw
import simplejson as json
from google.appengine.api import users
from ..decorators import login_required

API_VERSION = "2010-04-01"
TESTING = False

if TESTING:
	from ..credentials.test import (account, ACCOUNT_SID, PHONE_NUMBER)
else:
	from ..credentials import (account, ACCOUNT_SID, PHONE_NUMBER)

@app.route("/call/<route_id>/<stop_id>/<phone_num>")
@login_required
def call_prediction(route_id, stop_id, phone_num):
	user = users.get_current_user()
	app.logger.info("%s (%s) called %s" % (user.nickname(), user.user_id(), phone_num))
	call_info = {
		'From': PHONE_NUMBER,
		'To': phone_num,
		'Url': 'http://buscalling.appspot.com/predict/%s/%s.twiml' % \
			(route_id, stop_id),
	}
	try:
		call_json = account.request(
			'/%s/Accounts/%s/Calls.json' % (API_VERSION, ACCOUNT_SID),
			'GET', 
			call_info)
		app.logger.info(call_json)
		call = json.loads(call_json)
		return "Now calling %s with call ID %s" % (call['to'], call['sid'])
	except tw.HTTPErrorAppEngine, e:
		app.logger.error(e)
		try:
			err = json.loads(e.msg)
			message = err['Message']
			return "REMOTE ERROR: %s" % (message,)
		except:
			return "Couldn't parse error output:<br>\n%s" % e.msg

