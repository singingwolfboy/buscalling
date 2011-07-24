from functools import wraps
from google.appengine.api import users
from flask import redirect, request, abort

def login_required(func):
    """
    Indicates that a view requires a logged-in user. In order to play nicely
    with Flask's routing system, this decorator must sit between the view
    function itself and the @app.route() decorators. For example, 
    this is valid::

        @app.route('/hiya')
        @app.route('/hello')
        @login_required
        def hello():
            return "You're logged in!"
    
    but this is invalid::

        @login_required
        @app.route('/hiya')
        @app.route('/hello')
        def hello():
            return "I'm broken."
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not users.get_current_user():
            return redirect(users.create_login_url(request.url), 303)
        return func(*args, **kwargs)
    # @app.route() creates a url rule based on the name of the view function,
    # so we need to pull that information up and through this decorator.
    decorated_view.__name__ = func.__name__
    return decorated_view

def admin_required(func):
    """
    Indicates that view requires an admin user. Supersedes @login_required:
    no need to use both. Subject to the same routing restrictions.
    """
    @wraps(func)
    def decorated_view(*args, **kwargs):
        user = users.get_current_user()
        if not users.is_current_user_admin():
            abort(403)
        return func(*args, **kwargs)
    # @app.route() creates a url rule based on the name of the view function,
    # so we need to pull that information up and through this decorator.
    decorated_view.__name__ = func.__name__
    return decorated_view