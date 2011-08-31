from __future__ import absolute_import
"""
This file is run at the very beginning of every dynamic request. Note
that the first thing it must do is alter sys.path so that App Engine
can find the modules and eggs in the local lib directory.
"""
import os, sys

def get_updated_sys_path():
    """
    Returns sys.path prepended with the local lib path, as well as all eggs in
    the local lib directory. Does not actually modify sys.path.
    """
    # root_path is directory containing this file
    root_path = os.path.dirname(os.path.abspath(__file__))
    # lib_path is directory containing other Python modules and eggs
    lib_path = os.path.join(root_path, 'lib')
    eggs = [os.path.join(lib_path, f) for f in 
        os.listdir(lib_path) if f.endswith(".egg")]
    # stick lib_path in front of eggs, add the existing path to the end
    eggs.insert(0, lib_path)
    eggs.extend(sys.path)
    return eggs

def run_app():
    "Actually runs the Flask application."
    # Note that these import statements must be INSIDE the function 
    # definition, so that Python doesn't attempt to import until after
    # sys.path has been updated. Otherwise, they will fail!
    from buscall import app

    # If we're in development mode...
    if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
        # don't set app.debug here, already set in buscall/__init__.py

        # Enable Werkzeug debugger
        from werkzeug import DebuggedApplication
        app.wsgi_app = DebuggedApplication(app.wsgi_app, evalex=True)

        # Enable Jinja2 debugging
        from google.appengine.tools.dev_appserver import HardenedModulesHook
        HardenedModulesHook._WHITE_LIST_C_MODULES += ['_ctypes', 'gestalt']

    # Grab your middleware and wrap the app
    from middleware import MethodRewriteMiddleware
    app.wsgi_app = MethodRewriteMiddleware(app.wsgi_app)

    # Run the app using Werkzeug
    from google.appengine.ext.webapp.util import run_wsgi_app
    run_wsgi_app(app)

if __name__ == "__main__":
    sys.path = get_updated_sys_path()        
    run_app()
