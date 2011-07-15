from twilio_api import Account, Response
from buscall.credentials import ACCOUNT_SID, ACCOUNT_TOKEN, PHONE_NUMBER
from buscall.util import DOMAIN, pluralize_minutes, humanize_list
from flask import url_for
import simplejson as json

API_VERSION = "2010-04-01"
account = Account(ACCOUNT_SID, ACCOUNT_TOKEN)

def get_twiml(prediction):
    r = Response()
    buses = prediction.buses
    if len(buses) == 0:
        r.addSay("No buses predicted.", language="en")
        return str(r)
        
    first = buses[0]
    time = pluralize_minutes(first.minutes)
    say = "%s until %s bus arrives at %s, heading towards %s." % \
        (time.capitalize(), prediction.route.title, 
        prediction.stop.title, prediction.direction.title)
    r.addSay(say, language="en")
    
    if len(buses) == 1:
        say = "No more buses predicted."
    else:
        times_lst = []
        for bus in buses[1:]:
            times_lst.append(pluralize_minutes(bus.minutes))
        
        if len(times_lst) == 1:
            say = "One more bus coming in %s" % (times_lst[0])
        else:
            say = "%s more buses coming in %s" % (len(times_lst), humanize_list(times_lst))
    r.addSay(say, language="en")

    return str(r)

def alert_by_phone(listener):
    url = DOMAIN + url_for('predict_for_stop', 
        agency_id=listener.agency.id, 
        route_id=listener.route.id, 
        direction_id=listener.direction.id, 
        stop_id=listener.stop.id, 
        format="twiml")
    call_info = {
        'From': PHONE_NUMBER,
        'To': listener.userprofile.phone,
        'Url': url,
        'Method': 'GET',
    }
    return json.loads(account.request(
        '/%s/Accounts/%s/Calls.json' % (API_VERSION, ACCOUNT_SID),
        'POST', 
        call_info))
