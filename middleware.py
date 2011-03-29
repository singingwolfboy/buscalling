class HTTPMethodOverrideMiddleware(object):
    """
    With this middleware installed, a _method HTTP parameter will override
    the actual HTTP method used in making the request. For example, if
    a browser makes an HTTP POST request while specifying _method=PUT,
    it will be treated as a PUT request instead.
    
    This follows the convention established and used by Ruby on Rails
    (Rack::MethodOverride). It is designed for standard web browsers, 
    which can only submit HTTP forms using either the GET or POST methods.
    """
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        method = environ.get('_method')
        if method:
            environ['REQUEST_METHOD'] = method.upper()
        return self.app(environ, start_response)


class DummyMiddleware(object):
    "For testing purposes."
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        return self.app(*args, **kwargs)