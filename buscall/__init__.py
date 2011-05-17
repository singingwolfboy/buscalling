from flask import Flask
from flaskext.cache import Cache

app = Flask(__name__)
app.config['CACHE_TYPE'] = 'gaememcached'
app.config['CACHE_KEY_PREFIX'] = 'buscall|'
cache = Cache(app)

import buscall.views