import os
from flask import Flask
from flaskext.cache import Cache
from buscall.credentials import SECRET_KEY

app = Flask(__name__)
if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
    app.debug = True
app.secret_key = SECRET_KEY
app.config['CACHE_TYPE'] = 'gaememcached'
app.config['CACHE_KEY_PREFIX'] = 'buscall|'
cache = Cache(app)

import buscall.views