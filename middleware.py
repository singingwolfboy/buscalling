from werkzeug import Request
try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

class MethodRewriteMiddleware(object):
    """
    With this middleware installed, a _method HTTP parameter will override
    the actual HTTP method used in making the request. For example, if
    a browser makes an HTTP POST request while specifying _method=PUT,
    it will be treated as a PUT request instead.
    
    This follows the convention established and used by Ruby on Rails
    (Rack::MethodOverride). It is designed for standard web browsers, 
    which can only submit HTTP forms using either the GET or POST methods.
    """
    def __init__(self, app, input_name='_method'):
        self.app = app
        self.input_name = input_name

    def __call__(self, environ, start_response):
        pf = environ.get('wsgi.input', None)
        if not pf:
            return self.app(environ, start_response)

        params = parse_qs(pf.read())
        pf.seek(0)

        if self.input_name in params:
            method = params[self.input_name][0].upper()

            if method in ['GET', 'POST', 'PUT', 'DELETE']:
                environ['REQUEST_METHOD'] = method

        return self.app(environ, start_response)

class DummyMiddleware(object):
    "For testing purposes."
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        return self.app(*args, **kwargs)