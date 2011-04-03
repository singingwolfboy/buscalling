from buscall import app
import twilio_api as tw
from google.appengine.api import users
from ..decorators import login_required
from ..credentials import \
	ACCOUNT_SID, ACCOUNT_TOKEN, CALLER_ID

API_VERSION = "2010-04-01"

account = tw.Account(ACCOUNT_SID, ACCOUNT_TOKEN)

@app.route("/call")
@app.route("/call/<int:phone_num>")
@login_required
def test_call(phone_num="3015238533"):
	user = users.get_current_user()
	app.logger.info("%s (%s) called %s" % (user.nickname(), user.user_id(), phone_num))
	call_info = {
		'From': CALLER_ID,
		'To': phone_num,
		'Url': 'http://demo.twilio.com/welcome',
	}
	#return str(call_info)
	response = account.request(
		'/%s/Accounts/%s/Calls' % (API_VERSION, ACCOUNT_SID),
		'POST', 
		call_info)
	return str(response)