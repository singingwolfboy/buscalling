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

@app.route("/call")
@app.route("/call/<int:phone_num>")
@login_required
def test_call(phone_num="3015238533"):
	user = users.get_current_user()
	app.logger.info("%s (%s) called %s" % (user.nickname(), user.user_id(), phone_num))
	call_info = {
		'From': PHONE_NUMBER,
		'To': phone_num,
		'Url': 'http://demo.twilio.com/welcome',
	}
	try:
		call_json = account.request(
			'/%s/Accounts/%s/Calls.json' % (API_VERSION, ACCOUNT_SID),
			'POST', 
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
		except AttributeError:
			return "Couldn't parse error output:<br>\n%s" % e.msg

