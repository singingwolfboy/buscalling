from buscall import app
from flask import request, abort, flash, redirect, url_for
from urllib import urlencode
import datetime
import decimal
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs
from google.appengine.api import urlfetch, users, mail
from buscall.models.paypal import url as paypal_url
from buscall.models.paypal import pdt_token
from buscall.models.profile import UserProfile
from buscall.models.txn import Transaction
from buscall.decorators import login_required
from buscall.util import MAIL_SENDER

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
    
    # we need to return status code 200 to make PayPal happy,
    # and Flask needs some kind of response, so we'll just return an empty string.
    return ""

@app.route('/paypal/success')
@login_required
def paypal_success():
    "PayPal Payment Data Transfer handler"
    params = {
        "cmd": "_notify-synch",
        "at": pdt_token,
        "tx": request.args.get("tx", None),
    }
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, paypal_url,
        method="POST", payload=urlencode(params))

    user_id = request.args.get("cm", None)
    user = users.get_current_user()
    if user.user_id() != user_id:
        abort(401)
    profile = UserProfile.get_by_user(user)

    try:
        result = rpc.get_result()
        lines = result.content.splitlines()
        if lines[0] == "SUCCESS":
            # yay
            txn_info = parse_qs("&".join(lines[1:]))
            txn = Transaction(
                processor="paypal",
                id=txn_info['id'][0],
                userprofile=profile,
                date=datetime.strptime(txn_info['payment_date'][0], "%H:%M:%S %b %d, %Y %Z"),
                amount=decimal.Decimal(txn_info['payment_gross'][0]),
                subscription_id=txn_info['subscr_id'][0],
                payment_status=txn_info['payment_status'][0],
            )
            txn.put()
            # update the user to indicate that they have paid
            profile.paid = True
            profile.put()
            flash("Payment succeeded. Your listeners are now active. Thank you!")
        elif lines[0] == "FAIL":
            # boo
            flash("Payment failed.", category="error")
        else:
            app.logger.info("Got unexpected result from PayPal PDT validation: "+result.content)
    except urlfetch.DownloadError:
        # request timed out or failed.
        flash("Could not verify payment with Paypal. Please email contact@buscalling.com.")
        mail.send_mail(sender=MAIL_SENDER,
            to="BusCalling Admin <contact@buscalling.com>",
            subject="Error validating payment with Paypal",
            body="Error validating payment with Paypal for user %s, txn id %s" % (user.email, params["tx"]))
    
    return redirect(url_for('lander'), 303)