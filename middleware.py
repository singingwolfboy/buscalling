from werkzeug import url_decode

class MethodRewriteMiddleware(object):
    """
    Based on http://flask.pocoo.org/snippets/38/

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
        if self.input_name in environ.get('QUERY_STRING', ''):
            args = url_decode(environ['QUERY_STRING'])
            method = args.get(self.input_name)
            if method:
                method = method.encode('ascii', 'replace')
                environ['REQUEST_METHOD'] = method
        return self.app(environ, start_response)

class DummyMiddleware(object):
    "For testing purposes."
    def __init__(self, app):
        self.app = app

    def __call__(self, *args, **kwargs):
        return self.app(*args, **kwargs)
