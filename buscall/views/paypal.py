from buscall import app
from flask import request
from urllib import urlencode
from google.appengine.api import urlfetch

@app.route('/paypal/ipn', methods=['POST'])
def paypal_ipn(self):
    "PayPal Instant Payment Notification handler"
    # validate request with PayPal
    params = request.form.to_dict()
    params['cmd'] = "_notify-validate"
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, "https://www.paypal.com/cgi-bin/webscr",
        method="POST", payload=urlencode(params))
    
    try:
        result = rpc.get_result()
        if result.content == "VERIFIED":
            # yay
            pass
        elif result.content == "INVALID":
            # boo
            pass
        else:
            app.logger.info("Got unexpected result from PayPal IPN validation: "+result.content)
    except urlfetch.DownloadError:
        # request timed out or failed.
        pass
