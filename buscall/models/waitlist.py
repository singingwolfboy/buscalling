#from ndb import model
from google.appengine.ext import db

class WaitlistEntry(db.Model):
	email = db.EmailProperty(required=True)
	location = db.GeoPtProperty()
	ip = db.StringProperty()
	created = db.DateTimeProperty(required=True, auto_now_add=True)