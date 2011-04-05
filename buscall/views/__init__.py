from buscall import app
from flask import render_template
from .nextbus import index_routes, show_route, predict_for_stop
from .twilio import call_prediction
from google.appengine.api import memcache

@app.route('/')
def hello():
    return render_template('hello.html')

@app.route('/flush')
def flush():
    if memcache.flush_all():
        return "FLUSHED"
    else:
        return "FLUSH FAILED"