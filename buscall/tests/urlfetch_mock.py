#!/opt/local/bin/python2.5
try:
    from itertools import permutations
except ImportError:
    from itertools_backport import permutations
from gae_mock import ServiceTestCase
from buscall.models import nextbus
from buscall.util import url_params

class MockUrlfetchTestCase(ServiceTestCase):
    def setUp(self):
        super(MockUrlfetchTestCase, self).setUp()
        responses = {}

        params = {
            "a": "mbta",
            "r": "26",
            "d": "26_1_var1",
            "s": "492",
            "command": "predictions",
        }
        response = """<?xml version="1.0" encoding="utf-8" ?> 
<body copyright="All data copyright MBTA 2011."> 
<predictions agencyTitle="MBTA" routeTitle="26" routeTag="26" stopTitle="Washington St @ Fuller St" stopTag="492"> 
  <direction title="Ashmont Belt via Washington St."> 
  <prediction epochTime="1309470680100" seconds="1246" minutes="20" isDeparture="false" affectedByLayover="true" dirTag="26_1_var1" vehicle="2071" block="B21_15" tripTag="15041527" /> 
  <prediction epochTime="1309472480100" seconds="3106" minutes="51" isDeparture="false" affectedByLayover="true" dirTag="26_1_var1" vehicle="2071" block="B21_15" tripTag="15041529" /> 
  <prediction epochTime="1309473680100" seconds="4306" minutes="71" isDeparture="false" affectedByLayover="true" dirTag="26_1_var1" vehicle="2103" block="B26_27" tripTag="15041916" /> 
  </direction> 
</predictions> 
</body> 
"""
        for ordering in permutations(params.items()):
            url = nextbus.RPC_URL + url_params(ordering)
            responses[url] = response
        
        self.urlfetch_responses = responses