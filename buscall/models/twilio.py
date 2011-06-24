from twilio_api import Response

def get_twiml(prediction):
    r = Response()
    buses = prediction['buses']
    if len(buses) == 0:
        r.addSay("No buses predicted.", language="en")
        return str(r)
        
    first = buses[0]
    time = pluralize_minutes(first['minutes'])
    say = "%s until %s bus arrives at %s, heading towards %s." % \
        (time.capitalize(), prediction['route_title'], 
        prediction['stop_title'], prediction['direction'])
    r.addSay(say, language="en")
    
    if len(buses) == 1:
        say = "No more buses predicted."
    else:
        times_lst = []
        for bus in buses[1:]:
            times_lst.append(pluralize_minutes(bus['minutes']))
        
        if len(times_lst) == 1:
            say = "One more bus coming in %s" % (times_lst[0])
        else:
            say = "%s more buses coming in %s" % (len(times_lst), humanize_list(times_lst))
    r.addSay(say, language="en")

    return str(r)

def pluralize_minutes(minutes):
    if minutes == 0:
        return "less than a minute"
    elif minutes == 1:
        return "one minute"
    else:
        return "%s minutes" % (minutes)

def humanize_list(lst):
    if len(lst) == 0:
        return ""
    elif len(lst) == 1:
        return lst[0]
    elif len(lst) == 2:
        return " and ".join(lst)
    else:
        return ", ".join(lst[:-2]) + ", and ".join(lst[-2:])