import time
from buscall import app
from buscall.models.nextbus import get_predictions
from buscall.models.listeners import BusListener
from buscall.util import DAYS_OF_WEEK

@app.route('/tasks/poll')
def poll():
    """
    This function is the workhorse of the whole application. When called,
    it checks the current time, pulls listeners from the datastore that are
    currently active, and then polls the bus routes for those listeners.
    This function is designed to be run once a minute (or more!) through cron.
    """
    now = time.gmtime()
    # get all currently active listeners
    listeners = GqlQuery("SELECT * FROM BusListener WHERE :wday = True AND start <= :time AND end >= :time",
        wday=DAYS_OF_WEEK[now.tm_wday],
        time="TIME(%d, %d, %d)" % (now.tm_hour, now.tm_min, now.tm_sec))
    for listener in listeners:
        predictions = listener.get_predictions()
        
