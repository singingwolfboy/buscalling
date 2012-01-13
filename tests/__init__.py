#!/opt/local/bin/python2.7
import unittest
import os
import sys
os.environ['APPENGINE_RUNTIME'] = 'python' + \
        str(sys.version_info.major) + \
        str(sys.version_info.minor)

# test for GAE libs
try:
    from google.appengine.tools import dev_appserver
except ImportError:
    from dev_appserver import EXTRA_PATHS
    paths = set(EXTRA_PATHS)
    from remote_api_shell import EXTRA_PATHS
    paths.update(EXTRA_PATHS)
    sys.path = list(paths) + sys.path
    from google.appengine.tools import dev_appserver

def all_tests_suite():
    return unittest.TestLoader().loadTestsFromNames([
        'tests.test_buslistener',
        'tests.test_datastore',
        'tests.test_urlfetch',
        'tests.test_new_listener_form',
        'tests.test_smoke',
    ])

def main():
    # need to set AUTH_DOMAIN before we can create User objects
    # if not 'AUTH_DOMAIN' in os.environ:
    #     os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
    
    runner = unittest.TextTestRunner()
    suite = all_tests_suite()
    runner.run(suite)

if __name__ == '__main__':
    main()
