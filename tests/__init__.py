#!/opt/local/bin/python2.5
import unittest
import os
from buscall.util import AUTH_DOMAIN

def all_tests_suite():
    return unittest.TestLoader().loadTestsFromNames([
        'buscall.tests.test_buslistener',
        'buscall.tests.test_datastore',
        'buscall.tests.test_urlfetch',
        'buscall.tests.test_new_listener_form',
        'buscall.tests.test_smoke',
    ])

def main():
    # need to set AUTH_DOMAIN before we can create User objects
    if not 'AUTH_DOMAIN' in os.environ:
        os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
    
    runner = unittest.TextTestRunner()
    suite = all_tests_suite()
    runner.run(suite)

if __name__ == '__main__':
    main()
