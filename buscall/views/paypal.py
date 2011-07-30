from buscall import app
from flask import request, abort, flash, redirect, url_for
from urllib import urlencode
import decimal
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs
from google.appengine.api import urlfetch, users, mail
from buscall.models.paypal import url as paypal_url
from buscall.models.paypal import pdt_token, sandbox, parse_paypal_date
from buscall.models.profile import UserProfile
from buscall.models.txn import Subscription, Payment
from buscall.decorators import login_required
from buscall.util import MAIL_SENDER

@app.route('/paypal/ipn', methods=['POST'])
def paypal_ipn():
    "PayPal Instant Payment Notification handler"
    # validate request with PayPal
    params = request.form.to_dict()
    app.logger.debug(params)
    if not sandbox and params.get("test_ipn", False):
        # someone's trying to trick us...
        return ""
    params['cmd'] = "_notify-validate"
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, paypal_url,
        method="POST", payload=urlencode(params))
    
    try:
        result = rpc.get_result()
        if result.content == "VERIFIED":
            user_id = params['custom']
            profile = UserProfile.get_by_key_name(user_id)
            if not profile:
                app.logger.warn("UserProfile not found")
                abort(400)
            if 'payer_id' in params and hasattr(profile, "paypal_id"):
                if params['payer_id'] != profile.paypal_id:
                    app.logger.warn("UserProfile's PayPal ID (%s) did not match PayPal ID from request (%s)" % (profile.paypal_id, params['payer_id']))
                    abort(400)
            txn_type = params['txn_type']
            subscr_id = params['subscr_id']

            if txn_type == "subscr_signup":
                subscr = Subscription(
                    parent=profile,
                    processor="paypal",
                    subscription_id=subscr_id,
                    key_name="paypal|"+subscr_id,
                    active=True,
                    start_transaction_id=params['ipn_track_id'],
                    start_date=parse_paypal_date(params['subscr_date']),
                    amount=decimal.Decimal(params['payment_gross']),
                )
                subscr.put()
                profile.paid = True
                profile.put()

            elif txn_type == "subscr_payment":
                txn_id = params['txn_id']
                subscr = Subscription.get_by_key_name("paypal|"+subscr_id)
                if not subscr:
                    abort(400)
                pmt = Payment(
                    processor="paypal",
                    subscription=subscr,
                    transaction_id=txn_id,
                    key_name="paypal|"+txn_id,
                    date=parse_paypal_date(params['payment_date']),
                    amount=decimal.Decimal(params['payment_gross']),
                    status=params['payment_status'][0],
                )
                if 'ipn_track_id' in params:
                    pmt.track_id = params['ipn_track_id']
                pmt.put()
                
            elif txn_type == "subscr_cancel":
                subscr = Subscription.get_by_key_name("paypal|"+subscr_id)
                if not subscr:
                    abort(400)
                subscr.end_track_id = params['ipn_track_id']
                subscr.end_date = parse_paypal_date(params['subscr_date'])
                subscr.active = False
                subscr.put()
                profile = subscr.userprofile
                profile.paid = False
                profile.put()
            
            else:
                app.logger.info("Got unexpected transaction type from Paypal IPN: "+str(params))

        elif result.content == "INVALID":
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
            payer_id = txn_info['payer_id'][0]
            if not getattr(profile, "paypal_id", None):
                profile.paypal_id = payer_id
            if profile.paypal_id != payer_id:
                app.logger.warn("Got different PayPal ID for user %s: recorded ID is %s, but got %s" % (user, profile.paypal_id, payer_id))
                abort(401)
            txn_id = txn_info['txn_id'][0]
            subscr_id = txn_info['subscr_id'][0]
            txn_date = parse_paypal_date(txn_info['payment_date'][0])
            subscr = Subscription(
                parent=profile,
                processor="paypal",
                subscription_id=subscr_id,
                key_name="paypal|"+subscr_id,
                active=True,
                start_transaction_id=txn_id,
                start_date=txn_date,
                amount=decimal.Decimal(txn_info['payment_gross'][0]),
            )
            subscr.put()
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
            body="Error validating payment with Paypal for user %s. GET info:\n%s" % (user.email, str(request.args)))
    
    return redirect(url_for('lander'), 303)