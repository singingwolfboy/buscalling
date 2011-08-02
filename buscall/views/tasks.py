import time
import datetime
from google.appengine.ext.db import GqlQuery
from buscall import app
from buscall.models.nextbus import get_predictions
from buscall.models.listener import BusListener
from buscall.util import DAYS_OF_WEEK
from flask import redirect, url_for

@app.route('/tasks/poll')
def poll(struct_time=None):
    """
    This function is the workhorse of the whole application. When called,
    it checks the current time, pulls listeners from the datastore that are
    currently active, and then polls the bus routes for those listeners.
    This function is designed to be run once a minute (or more!) through cron.
    """
    if struct_time is None:
        struct_time = time.localtime() # current time

    # get all currently active listeners
    listeners = GqlQuery("SELECT * FROM BusListener WHERE " +
        DAYS_OF_WEEK[struct_time.tm_wday] + " = True AND start <= :time AND seen = False",
        time="TIME(%d, %d, %d)" % (struct_time.tm_hour, struct_time.tm_min, struct_time.tm_sec))
    for listener in listeners:
        if not listener.start <= datetime.time(struct_time.tm_hour, struct_time.tm_min, struct_time.tm_sec):
            continue # should have been filtered out by GqlQuery, but wasn't
        predictions = listener.get_predictions()
        for alert in listener.alerts:
            for bus in predictions.buses:
                if alert.minutes == bus.minutes:
                    alert.execute(bus.minutes)
    
    return redirect(url_for("lander"), 303)

@app.route('/tasks/reset_seen_flags')
def reset_seen_flags():
    seen = GqlQuery("SELECT * FROM BusListener WHERE seen = True")
    for listener in seen:
        listener.seen = False
        listener.put()
    executed = GqlQuery("SELECT * FROM BusAlert WHERE executed = True")
    from alert in executed:
        alert.executed = False
        alert.put()
    return redirect(url_for("lander"), 303)
