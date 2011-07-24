from buscall import app
from flask import request, abort, flash, redirect, url_for
from urllib import urlencode
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs
from google.appengine.api import urlfetch, users
from buscall.models.paypal import url as paypal_url
from buscall.models.paypal import pdt_token
from buscall.models.profile import UserProfile
from buscall.decorators import login_required

@app.route('/paypal/ipn', methods=['POST'])
def paypal_ipn():
    "PayPal Instant Payment Notification handler"
    # validate request with PayPal
    params = request.form.to_dict()
    app.logger.debug(params)
    params['cmd'] = "_notify-validate"
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, paypal_url,
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

@app.route('/paypal/success')
@login_required
def paypal_success():
    "PayPal Payment Data Transfer handler"
    params = {
        "cmd": "_notify-synch",
        "at": pdt_token,
        "tx": request.form.get("tx", None),
    }
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, paypal_url,
        method="POST", payload=urlencode(params))

    user_id = request.form.get("cm", None)
    user = users.get_current_user()
    if not user.user_id() == user_id:
        abort(401)
    profile = UserProfile.get_by_user(user)

    try:
        result = rpc.get_result()
        lines = result.content.splitlines()
        if lines[0] == "SUCCESS":
            # yay
            txn = parse_qs("&".join(lines[1:]))
            app.logger.debug(txn)
            flash("Payment Success: " + txn)
        elif lines[0] == "FAIL":
            # boo
            flash("Payment Failed", category="error")
        else:
            app.logger.info("Got unexpected result from PayPal PDT validation: "+result.content)
    except urlfetch.DownloadError:
        # request timed out or failed.
        pass
    
    return redirect(url_for('lander'), 303)