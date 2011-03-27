# first, we need to manipulate the Python path. The order should be:
#   local lib dir
#   eggs in local lib dir
#   existing path entries
import sys
import os
root_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(root_dir, 'lib')
eggs = [os.path.join(lib_dir, f) for f in 
    os.listdir(lib_dir) if f.endswith(".egg")]
# stick lib dir in front of eggs, and add the existing path to the end
eggs.insert(0, lib_dir)
eggs.extend(sys.path)
# and replace
sys.path = eggs


# import our app
from buscall import app
# wrap it in a middleware
from middleware import OverrideHTTPVerbMiddleware
app.wsgi_app = OverrideHTTPVerbMiddleware(app.wsgi_app)
# and run it
try:
    # on werkzeug if we can
    if os.environ.get('SERVER_SOFTWARE').startswith('Dev'):
        # only use debug mode in dev mode
        from werkzeug_debugger_appengine import get_debugged_app
        app.debug=True
        app = get_debugged_app(app)
    from wsgiref.handlers import CGIHandler
    CGIHandler().run(app)
except ImportError:
    # or fall back on webapp
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(app)
    
