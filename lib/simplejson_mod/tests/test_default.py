from unittest import TestCase

import simplejson_mod as json

class TestDefault(TestCase):
    def test_default(self):
        self.assertEquals(
            json.dumps(type, default=repr),
            json.dumps(repr(type)))
