import unittest
import doctest


class OptionalExtensionTestSuite(unittest.TestSuite):
    def run(self, result):
        import simplejson_mod
        run = unittest.TestSuite.run
        run(self, result)
        simplejson_mod._toggle_speedups(False)
        run(self, result)
        simplejson_mod._toggle_speedups(True)
        return result


def additional_tests(suite=None):
    import simplejson_mod
    import simplejson_mod.encoder
    import simplejson_mod.decoder
    if suite is None:
        suite = unittest.TestSuite()
    for mod in (simplejson_mod, simplejson_mod.encoder, simplejson_mod.decoder):
        suite.addTest(doctest.DocTestSuite(mod))
    #suite.addTest(doctest.DocFileSuite('../../index.rst'))
    return suite


def all_tests_suite():
    suite = unittest.TestLoader().loadTestsFromNames([
        'simplejson_mod.tests.test_check_circular',
        'simplejson_mod.tests.test_decode',
        'simplejson_mod.tests.test_default',
        'simplejson_mod.tests.test_dump',
        'simplejson_mod.tests.test_encode_basestring_ascii',
        'simplejson_mod.tests.test_encode_for_html',
        'simplejson_mod.tests.test_errors',
        'simplejson_mod.tests.test_fail',
        'simplejson_mod.tests.test_float',
        'simplejson_mod.tests.test_indent',
        'simplejson_mod.tests.test_pass1',
        'simplejson_mod.tests.test_pass2',
        'simplejson_mod.tests.test_pass3',
        'simplejson_mod.tests.test_recursion',
        'simplejson_mod.tests.test_scanstring',
        'simplejson_mod.tests.test_separators',
        'simplejson_mod.tests.test_speedups',
        'simplejson_mod.tests.test_unicode',
        'simplejson_mod.tests.test_decimal',
    ])
    suite = additional_tests(suite)
    return OptionalExtensionTestSuite([suite])


def main():
    runner = unittest.TextTestRunner()
    suite = all_tests_suite()
    runner.run(suite)


if __name__ == '__main__':
    import os
    import sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    main()
