import sys
from main import get_updated_sys_path
sys.path = get_updated_sys_path()

from flaskext.script import Shell, Manager

from buscall import app, models, views, forms
from google.appengine.ext import db

from credentials import SECRET_KEY
app.secret_key = SECRET_KEY

def _make_context():
    return {
        "app": app,
        "models": models,
        "views": views,
        "forms": forms,
        "db": db,
    }

manager = Manager(app)
manager.add_command("shell", Shell(make_context=_make_context))

if __name__ == "__main__":
    manager.run()