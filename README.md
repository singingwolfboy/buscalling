BUS CALLING
===========
Time management before the coffee kicks in.
-------------------------------------------

Bus Calling allows you to sign up for alerts for bus systems
with API access. It's a Flask-based application designed to
run on the Python 2.7 runtime of Google App Engine. 
Most runtime dependencies are packaged in the `lib` directory,
but App Engine provides a few libraries on production that
you need to install on the development environment:

* [lxml][lxml]
* [jinja2][jinja2]

For testing, you'll also need:

* [fixture][fixture]

To compile the static resources, you'll need:

* [compass][compass]
* [coffeescript][coffee]

I recommend using [LiveReload][livereload] to manage
these files during development.

To use the `cache_nextbus.py` script to load XML files from Nextbus
for testing, you'll also need:

* [requests][requests]
* [gevent][gevent]
* [eventlet][eventlet]

[lxml]: http://lxml.de
[jinja2]: http://jinja.pocoo.org
[fixture]: http://farmdev.com/projects/fixture/
[compass]: http://compass-style.org
[coffee]: http://coffeescript.org
[livereload]: http://livereload.com
[requests]: python-requests.org
[gevent]: http://www.gevent.org
[eventlet]: http://www.eventlet.net
