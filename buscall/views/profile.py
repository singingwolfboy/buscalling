from buscall import app
from flask import render_template
from ..decorators import login_required
from google.appengine.api import users
from buscall.models.profile import BusListener
from google.appengine.ext.db import GqlQuery as TruthyGqlQuery

class GqlQuery(TruthyGqlQuery):
    def __nonzero__(self):
        return self.count(1) != 0

@app.route('/listeners')
@login_required
def index_listeners():
    import gae_pdb
    gae_pdb.set_trace()
    listeners = GqlQuery("SELECT * FROM BusListener WHERE user = :1", 
        users.get_current_user())
    return render_template('listeners/index.html', listeners=listeners)
