#from flaskext import wtf
from buscall.models import WaitlistEntry
from wtforms.ext.appengine.db import model_form

WaitlistForm = model_form(WaitlistEntry)