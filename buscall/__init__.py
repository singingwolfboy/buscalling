import os
from flask import Flask
from werkzeug import ImmutableDict
from flaskext.cache import Cache
from buscall.credentials import SECRET_KEY

app = Flask(__name__)
if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
    app.debug = True
app.secret_key = SECRET_KEY
app.config['CACHE_TYPE'] = 'gaememcached'
app.config['CACHE_KEY_PREFIX'] = 'buscall|'
cache = Cache(app)

app.jinja_options = ImmutableDict(
    extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_', 'jinja2.ext.do']
)

import buscall.views
