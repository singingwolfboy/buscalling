from buscall import app
from flask import request, abort, flash, redirect, url_for
from urllib import urlencode
from decimal import Decimal
try:
    from urlparse import parse_qsl
except ImportError:
    from cgi import parse_qsl
from google.appengine.api import urlfetch, mail
from buscall.models.paypal import url as paypal_url
from buscall.models.paypal import pdt_token, sandbox, parse_paypal_date, item_map
from buscall.models.user import User
from buscall.models.txn import Subscription, Payment
from buscall.decorators import login_required
from buscall.util import MAIL_SENDER
from ndb import Key

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
            user_key = Key(User, user_id)
            user = user_key.get()
            if not user:
                app.logger.warn("User not found")
                abort(400)
            if 'payer_id' in params and hasattr(user, "paypal_id"):
                if params['payer_id'] != user.paypal_id:
                    app.logger.warn("User's PayPal ID (%s) did not match PayPal ID from request (%s)" % (user.paypal_id, params['payer_id']))
                    abort(400)
            txn_type = params['txn_type']

            # SUBSCRIPTION SIGNUP
            if txn_type == "subscr_signup":
                subscr_id = params['subscr_id']
                # create or update Subscription object
                subscr_key = Key(Subscription, "paypal|"+subscr_id)
                subscr = subscr_key.get()
                if subscr:
                    subscr.start_track_id=params['ipn_track_id']
                    subscr.start_date=parse_paypal_date(params['subscr_date'])
                    subscr.put()
                else:
                    subscr = Subscription(
                        key=subscr_key,
                        user_key=user_key,
                        processor="paypal",
                        subscription_id=subscr_id,
                        active=True,
                        start_track_id=params['ipn_track_id'],
                        start_date=parse_paypal_date(params['subscr_date']),
                        amount=Decimal(params['amount3']),
                    )
                    subscr.put()
                user.freeloader = False
                user.subscribed = True
                user.put()

            # PAYMENT ON A SUBSCRIPTION
            elif txn_type == "subscr_payment":
                subscr_id = params['subscr_id']
                subscr_key = Key(Subscription, "paypal|"+subscr_id)
                subscr = subscr_key.get()
                # get or create Subscription object
                txn_id = params['txn_id']
                if not subscr:
                    subscr = Subscription(
                        key=subscr_key,
                        user_key=user_key,
                        processor="paypal",
                        subscription_id=subscr_id,
                        active=True,
                        start_track_id=params['ipn_track_id'],
                        start_date=parse_paypal_date(params['payment_date']),
                        amount=Decimal(params['payment_gross']),
                    )
                    subscr.put()

                # create Payment object
                pmt_key = Key(Payment, "paypal|"+txn_id)
                pmt = Payment(
                    key=pmt_key,
                    processor="paypal",
                    subscription=subscr,
                    transaction_id=txn_id,
                    date=parse_paypal_date(params['payment_date']),
                    amount=Decimal(params['payment_gross']),
                    status=params['payment_status'],
                )
                if 'ipn_track_id' in params:
                    pmt.track_id = params['ipn_track_id']
                pmt.put()
                
            # END OF SUBSCRIPTION
            elif txn_type == "subscr_cancel":
                subscr_id = params['subscr_id']
                subscr_key = Key(Subscription, "paypal|"+subscr_id)
                subscr = subscr_key.get()
                if not subscr:
                    app.logger.warn("Could not find Subscription: paypal|"+subscr_id)
                    abort(400)
                subscr.end_track_id = params['ipn_track_id']
                subscr.end_date = parse_paypal_date(params['subscr_date'])
                subscr.active = False
                subscr.put()
                user = subscr.user_key.get()
                user.subscribed = False
                user.put()
            
            # "BUY NOW" BUTTON
            elif txn_type == "web_accept":
                txn_id = params['txn_id']
                pmt_key = Key(Payment, "paypal|"+txn_id)
                pmt = pmt_key.get()
                item_num = int(params['item_number'])
                quantity = int(params.get('quantity', 1))
                if not pmt:
                    pmt = Payment(
                        key=pmt_key,
                        processor="paypal",
                        subscription=None,
                        transaction_id=txn_id,
                        date=parse_paypal_date(params['payment_date']),
                        amount=Decimal(params['payment_gross']),
                        status=params['payment_status'],
                        item_id=item_num,
                        quantity=quantity,
                    )
                # update fields regardless
                if 'payment_status' in params:
                    pmt.status = params['payment_status']
                if 'ipn_track_id' in params:
                    pmt.track_id = params['ipn_track_id']
                if 'payment_gross' in params:
                    pmt.amount = Decimal(params['payment_gross'])

                pmt.put()

                # how many credits did the user buy?
                for item_id, (item_cost, credits) in item_map.items():
                    if item_num == item_id:
                        # if ID matches, that's enough; but if the price doesn't match as well,
                        # log a warning
                        if not pmt.amount == item_cost * quantity:
                            warning = "Paypal IPN: got item number %s (qty %s) but paid %s" % (item_num, quantity, pmt.amount)
                            warning += "\n" + str(params)
                            app.logger.warn(warning)
                        # either way, increment the user's credit balance
                        user.credits += credits * quantity
                        user.freeloader = False
                        user.put()
                        break
            
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
    app.logger.debug(request.args.to_dict())
    params = {
        "cmd": "_notify-synch",
        "at": pdt_token,
        "tx": request.args.get("tx", None),
    }
    rpc = urlfetch.create_rpc()
    urlfetch.make_fetch_call(rpc, paypal_url,
        method="POST", payload=urlencode(params))

    user_id = request.args.get("cm", None)
    user_key = Key(User, user_id)
    user = user_key.get()
    if not user.matches_current_google_user():
        abort(401)

    try:
        result = rpc.get_result()
        lines = result.content.splitlines()
        if lines[0] == "SUCCESS":
            txn_info = dict(parse_qsl("&".join(lines[1:])))
            payer_id = txn_info['payer_id']
            if not getattr(user, "paypal_id", None):
                user.paypal_id = payer_id
            if user.paypal_id != payer_id:
                app.logger.warn("Got different PayPal ID for user %s: recorded ID is %s, but got %s" % (user, user.paypal_id, payer_id))
                abort(401)
            txn_id = txn_info['txn_id']

            subscr_id = txn_info.get('subscr_id')
            txn_date = parse_paypal_date(txn_info['payment_date'])
            amount = Decimal(txn_info['payment_gross'])

            # was this a subscription signup, or a credit purchase?
            if subscr_id:
                # find or create the Subscription object
                subscr_key = Key(Subscription, "paypal|" + subscr_id)
                subscr = subscr_key.get()
                if not subscr:
                    subscr = Subscription(
                        key=subscr_key,
                        user_key=user.key,
                        processor="paypal",
                        subscription_id=subscr_id,
                        active=True,
                        start_date=txn_date,
                        amount=amount,
                    )
                    subscr.put()
            else:
                subscr = None
            
            # create the Payment object
            pmt_key = Key(Payment, "paypal|"+txn_id)
            pmt = pmt_key.get()
            if pmt:
                pmt_seen = True
            else:
                pmt_seen = False
                pmt = Payment(
                    key=pmt_key,
                    subscription_key=subscr.key,
                    processor="paypal",
                    transaction_id=txn_id,
                    date=txn_date,
                    amount=amount,
                    status=txn_info['payment_status'],
                )
            if 'item_number' in txn_info:
                pmt.item_id = int(txn_info['item_number'])
            if 'quantity' in txn_info:
                pmt.quantity = int(txn_info['quantity'])
            if 'ipn_track_id' in txn_info:
                pmt.track_id = txn_info['ipn_track_id']
            pmt.put()

            # update the user
            user.freeloader = False
            if subscr:
                user.subscribed = True
                msg = "Payment succeeded. Your listeners are now active. Thank you!"
            else:
                # we increment credits on IPN, not PDT
                if pmt_seen:
                    msg = "Payment succeeded. Your pickup balance has been updated. Thank you!"
                else:
                    msg = "Your pickup balance will be updated when we receive confirmation from PayPal. Thank you!"
            user.put()
            flash(msg, category="success")
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
