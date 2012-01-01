import time
import datetime
from google.appengine.ext.db import GqlQuery
from buscall import app
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
        for notification in listener.notifications:
            for bus in predictions:
                if notification.minutes == bus.minutes:
                    notification.execute(bus.minutes)
    
    return redirect(url_for("lander"), 303)

@app.route('/tasks/reset_seen_flags')
def reset_seen_flags():
    seen = GqlQuery("SELECT * FROM BusListener WHERE seen = True")
    for listener in seen:
        if listener.recur:
            # reset the "seen" flag
            listener.seen = False
            listener.put()
        else:
            # the listener has run, and it shouldn't run again, so delete it
            listener.delete()
    executed = GqlQuery("SELECT * FROM BusNotification WHERE executed = True")
    for notification in executed:
        notification.executed = False
        notification.put()
    return redirect(url_for("lander"), 303)
