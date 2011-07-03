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

        # routeConfig for route 26
        params = {
            "a": "mbta",
            "r": "26",
            "command": "routeConfig",
        }
        response = """<?xml version="1.0" encoding="utf-8" ?> 
<body copyright="All data copyright MBTA 2011."> 
<route tag="26" title="26" color="999933" oppositeColor="000000" latMin="42.27802" latMax="42.29019" lonMin="-71.08697" lonMax="-71.0643"> 
<stop tag="507" title="Gallivan Blvd @ Morton St" lat="42.2786399" lon="-71.07972" stopId="00507"/> 
<stop tag="508" title="Gallivan Blvd opp Arbella Rd" lat="42.2782799" lon="-71.0767599" stopId="00508"/> 
<stop tag="509" title="Gallivan Blvd @ Oakridge St" lat="42.2780799" lon="-71.0748699" stopId="00509"/> 
<stop tag="510" title="Gallivan Blvd @ Pleasant Hill Ave" lat="42.27802" lon="-71.07257" stopId="00510"/> 
<stop tag="511" title="Washington St @ Gallivan Blvd" lat="42.2789599" lon="-71.0695299" stopId="00511"/> 
<stop tag="512" title="924 Washington St opp Codman Hill Ave" lat="42.2800699" lon="-71.0702099" stopId="00512"/> 
<stop tag="514" title="Washington St @ Coolidge Rd" lat="42.28117" lon="-71.07085" stopId="00514"/> 
<stop tag="515" title="Washington St @ Fuller St" lat="42.2819199" lon="-71.0711699" stopId="00515"/> 
<stop tag="516" title="Washington St @ Burt St" lat="42.2834399" lon="-71.0714" stopId="00516"/> 
<stop tag="517" title="776 Washington St opp Armadine St" lat="42.2846199" lon="-71.07143" stopId="00517"/> 
<stop tag="518" title="Washington St @ Ashmont St" lat="42.28548" lon="-71.07109" stopId="00518"/> 
<stop tag="519" title="Washington St @ Walton St" lat="42.28716" lon="-71.07117" stopId="00519"/> 
<stop tag="437" title="Washington St @ Welles Ave" lat="42.28809" lon="-71.07108" stopId="00437"/> 
<stop tag="4374" title="Washington St @ Lithgow St" lat="42.2895" lon="-71.07131" stopId="04374"/> 
<stop tag="426" title="Talbot Ave @ Lithgow St" lat="42.2899199" lon="-71.0697999" stopId="00426"/> 
<stop tag="427" title="Talbot Ave @ Brent St" lat="42.2896" lon="-71.0685" stopId="00427"/> 
<stop tag="428" title="Talbot Ave @ Welles Ave" lat="42.2890699" lon="-71.0671699" stopId="00428"/> 
<stop tag="429" title="493 Talbot Ave opp Argyle St" lat="42.28776" lon="-71.06544" stopId="00429"/> 
<stop tag="430" title="Talbot Ave @ Dorchester Ave" lat="42.2858" lon="-71.06439" stopId="00430"/> 
<stop tag="334_ar" title="Ashmont Station" lat="42.2846499" lon="-71.06449"/> 
<stop tag="494" title="Gallivan Blvd @ Washington St" lat="42.2785099" lon="-71.07051" stopId="00494"/> 
<stop tag="501" title="Gallivan Blvd @ Nevada St" lat="42.2781299" lon="-71.07243" stopId="00501"/> 
<stop tag="497" title="Gallivan Blvd @ Milton Ave" lat="42.27819" lon="-71.07492" stopId="00497"/> 
<stop tag="498" title="Gallivan Blvd @ Arbella Rd" lat="42.27839" lon="-71.07682" stopId="00498"/> 
<stop tag="499" title="Galivan Blvd @ Wilmington St" lat="42.2787399" lon="-71.0797599" stopId="00499"/> 
<stop tag="539" title="980 Morton St opp Owen St" lat="42.2793799" lon="-71.0809399" stopId="00539"/> 
<stop tag="540" title="Morton St @ Selden St" lat="42.2803599" lon="-71.0823899" stopId="00540"/> 
<stop tag="10540" title="Morton St @ Evans St" lat="42.2808899" lon="-71.08466" stopId="10540"/> 
<stop tag="445" title="Norfolk St @ Morton St" lat="42.2821899" lon="-71.08625" stopId="00445"/> 
<stop tag="446" title="Norfolk St @ Nelson St" lat="42.28348" lon="-71.0830499" stopId="00446"/> 
<stop tag="447" title="Norfolk St @ Capen St" lat="42.28416" lon="-71.08123" stopId="00447"/> 
<stop tag="448" title="Norfolk St. @ Stanton St. opp. #227" lat="42.28536" lon="-71.0804" stopId="00448"/> 
<stop tag="449" title="Norfolk St @ Thetford Ave" lat="42.2862199" lon="-71.07959" stopId="00449"/> 
<stop tag="450" title="Norfolk St @ Milton Ave" lat="42.2872099" lon="-71.07864" stopId="00450"/> 
<stop tag="451" title="Norfolk St opposite Woodrow Ave" lat="42.2879099" lon="-71.0779" stopId="00451"/> 
<stop tag="452" title="Norfolk St @ Peacevale Rd" lat="42.2882199" lon="-71.0766" stopId="00452"/> 
<stop tag="453" title="Norfolk St @ Chipman St" lat="42.28878" lon="-71.0748399" stopId="00453"/> 
<stop tag="454" title="Norfolk St @ Withington St" lat="42.2891699" lon="-71.07313" stopId="00454"/> 
<stop tag="455" title="Norfolk St @ Epping St" lat="42.2898099" lon="-71.07239" stopId="00455"/> 
<stop tag="334" title="Ashmont Station" lat="42.2846499" lon="-71.06449" stopId="00334"/> 
<stop tag="367" title="Talbot Ave @ Dorchester Ave" lat="42.2858899" lon="-71.0643" stopId="00367"/> 
<stop tag="368" title="Talbot Ave @ Argyle St" lat="42.28802" lon="-71.06551" stopId="00368"/> 
<stop tag="369" title="Talbot Ave @ Welles Ave" lat="42.2890399" lon="-71.0668699" stopId="00369"/> 
<stop tag="370" title="Talbot Ave @ Brent St" lat="42.2895899" lon="-71.0681899" stopId="00370"/> 
<stop tag="371" title="Talbot Ave @ Centre St" lat="42.29019" lon="-71.07098" stopId="00371"/> 
<stop tag="431" title="355 Norfolk St opp Withington St" lat="42.2893499" lon="-71.073" stopId="00431"/> 
<stop tag="432" title="Norfolk St @ Darlington St" lat="42.2886999" lon="-71.07548" stopId="00432"/> 
<stop tag="434" title="Norfolk St @ New England Ave" lat="42.2880699" lon="-71.07776" stopId="00434"/> 
<stop tag="435" title="Norfolk St @ Milton Ave" lat="42.28721" lon="-71.0787899" stopId="00435"/> 
<stop tag="436" title="Norfolk St @ Charles Rd" lat="42.28642" lon="-71.0795499" stopId="00436"/> 
<stop tag="438" title="227 Norfolk St opp Stanton St" lat="42.2855699" lon="-71.08038" stopId="00438"/> 
<stop tag="439" title="247 Norfolk St opp Capen St" lat="42.28421" lon="-71.0813599" stopId="00439"/> 
<stop tag="440" title="Norfolk St opp Nelson St" lat="42.28353" lon="-71.0831799" stopId="00440"/> 
<stop tag="441" title="Norfolk St @ Willowwood St" lat="42.28271" lon="-71.0852699" stopId="00441"/> 
<stop tag="443" title="Norfolk St @ Morton St" lat="42.2816899" lon="-71.08697" stopId="00443"/> 
<stop tag="529" title="Morton St opp Evans St" lat="42.28078" lon="-71.08462" stopId="00529"/> 
<stop tag="530" title="Morton St @ W Selden St" lat="42.28041" lon="-71.0828499" stopId="00530"/> 
<stop tag="531" title="Morton St @ Owen St" lat="42.27927" lon="-71.08096" stopId="00531"/> 
<stop tag="507_ar" title="Gallivan Blvd @ Morton St" lat="42.2786399" lon="-71.07972"/> 
<stop tag="37111" title="Washington St opp Lithgow St" lat="42.2894199" lon="-71.0714" stopId="37111"/> 
<stop tag="487" title="675 Washington St opp Welles Ave" lat="42.28804" lon="-71.0712199" stopId="00487"/> 
<stop tag="488" title="703 Washington St opp Walton St" lat="42.2873499" lon="-71.07129" stopId="00488"/> 
<stop tag="489" title="Washington St opp Ashmont St" lat="42.2854299" lon="-71.07123" stopId="00489"/> 
<stop tag="490" title="Washington St @ Armadine St" lat="42.2845899" lon="-71.07157" stopId="00490"/> 
<stop tag="491" title="Washington St @ Stockton St" lat="42.2831699" lon="-71.07148" stopId="00491"/> 
<stop tag="492" title="Washington St @ Fuller St" lat="42.28208" lon="-71.07135" stopId="00492"/> 
<stop tag="493" title="Washington St @ Ogden St" lat="42.28132" lon="-71.07104" stopId="00493"/> 
<stop tag="495" title="Washington St @ Codman Hill Ave" lat="42.27998" lon="-71.07029" stopId="00495"/> 
<stop tag="494_ar" title="Gallivan Blvd @ Washington St" lat="42.2785099" lon="-71.07051"/> 
<direction tag="26_1_var1" title="Ashmont Belt via Washington St." name="Inbound" useForUI="true"> 
  <stop tag="334" /> 
  <stop tag="367" /> 
  <stop tag="368" /> 
  <stop tag="369" /> 
  <stop tag="370" /> 
  <stop tag="371" /> 
  <stop tag="37111" /> 
  <stop tag="487" /> 
  <stop tag="488" /> 
  <stop tag="489" /> 
  <stop tag="490" /> 
  <stop tag="491" /> 
  <stop tag="492" /> 
  <stop tag="493" /> 
  <stop tag="495" /> 
  <stop tag="494_ar" /> 
</direction> 
<direction tag="26_0_var1" title="Ashmont Belt via Washington St." name="Outbound" useForUI="true"> 
  <stop tag="494" /> 
  <stop tag="501" /> 
  <stop tag="497" /> 
  <stop tag="498" /> 
  <stop tag="499" /> 
  <stop tag="539" /> 
  <stop tag="540" /> 
  <stop tag="10540" /> 
  <stop tag="445" /> 
  <stop tag="446" /> 
  <stop tag="447" /> 
  <stop tag="448" /> 
  <stop tag="449" /> 
  <stop tag="450" /> 
  <stop tag="451" /> 
  <stop tag="452" /> 
  <stop tag="453" /> 
  <stop tag="454" /> 
  <stop tag="455" /> 
  <stop tag="426" /> 
  <stop tag="427" /> 
  <stop tag="428" /> 
  <stop tag="429" /> 
  <stop tag="430" /> 
  <stop tag="334_ar" /> 
</direction> 
<direction tag="26_1_var0" title="Ashmont Belt via Norfolk St." name="Inbound" useForUI="true"> 
  <stop tag="334" /> 
  <stop tag="367" /> 
  <stop tag="368" /> 
  <stop tag="369" /> 
  <stop tag="370" /> 
  <stop tag="371" /> 
  <stop tag="431" /> 
  <stop tag="432" /> 
  <stop tag="434" /> 
  <stop tag="435" /> 
  <stop tag="436" /> 
  <stop tag="438" /> 
  <stop tag="439" /> 
  <stop tag="440" /> 
  <stop tag="441" /> 
  <stop tag="443" /> 
  <stop tag="529" /> 
  <stop tag="530" /> 
  <stop tag="531" /> 
  <stop tag="507_ar" /> 
</direction> 
<direction tag="26_0_var0" title="Ashmont Belt via Norfolk St." name="Outbound" useForUI="true"> 
  <stop tag="507" /> 
  <stop tag="508" /> 
  <stop tag="509" /> 
  <stop tag="510" /> 
  <stop tag="511" /> 
  <stop tag="512" /> 
  <stop tag="514" /> 
  <stop tag="515" /> 
  <stop tag="516" /> 
  <stop tag="517" /> 
  <stop tag="518" /> 
  <stop tag="519" /> 
  <stop tag="437" /> 
  <stop tag="4374" /> 
  <stop tag="426" /> 
  <stop tag="427" /> 
  <stop tag="428" /> 
  <stop tag="429" /> 
  <stop tag="430" /> 
  <stop tag="334_ar" /> 
</direction> 
<path> 
<point lat="42.28917" lon="-71.07313"/> 
<point lat="42.28926" lon="-71.07306"/> 
<point lat="42.28934" lon="-71.07292"/> 
<point lat="42.28944" lon="-71.0728"/> 
<point lat="42.28981" lon="-71.07239"/> 
<point lat="42.29002" lon="-71.07223"/> 
<point lat="42.2902" lon="-71.072"/> 
<point lat="42.29" lon="-71.06985"/> 
<point lat="42.28992" lon="-71.0698"/> 
<point lat="42.2896" lon="-71.0685"/> 
<point lat="42.28915" lon="-71.0672"/> 
<point lat="42.28907" lon="-71.06717"/> 
<point lat="42.2886499" lon="-71.06634"/> 
<point lat="42.2879999" lon="-71.0655699"/> 
<point lat="42.28776" lon="-71.06544"/> 
<point lat="42.28618" lon="-71.06448"/> 
<point lat="42.2858" lon="-71.06439"/> 
<point lat="42.28571" lon="-71.0643"/> 
<point lat="42.28465" lon="-71.06449"/> 
</path> 
<path> 
<point lat="42.28089" lon="-71.08466"/> 
<point lat="42.28111" lon="-71.08601"/> 
<point lat="42.28134" lon="-71.08651"/> 
<point lat="42.28164" lon="-71.08698"/> 
<point lat="42.28219" lon="-71.08625"/> 
</path> 
<path> 
<point lat="42.2846199" lon="-71.07143"/> 
<point lat="42.28533" lon="-71.07118"/> 
<point lat="42.28548" lon="-71.07109"/> 
<point lat="42.28598" lon="-71.07115"/> 
<point lat="42.28626" lon="-71.07117"/> 
<point lat="42.2866799" lon="-71.07117"/> 
<point lat="42.28689" lon="-71.0712099"/> 
<point lat="42.28716" lon="-71.0712099"/> 
<point lat="42.28716" lon="-71.07117"/> 
<point lat="42.28725" lon="-71.07122"/> 
<point lat="42.2880899" lon="-71.07108"/> 
<point lat="42.28851" lon="-71.07111"/> 
<point lat="42.28935" lon="-71.07132"/> 
<point lat="42.2894999" lon="-71.07131"/> 
<point lat="42.2902" lon="-71.0716"/> 
<point lat="42.29" lon="-71.06985"/> 
<point lat="42.28992" lon="-71.0698"/> 
<point lat="42.2896" lon="-71.0685"/> 
<point lat="42.28915" lon="-71.0672"/> 
<point lat="42.28907" lon="-71.06717"/> 
<point lat="42.2886499" lon="-71.06634"/> 
<point lat="42.2879999" lon="-71.0655699"/> 
<point lat="42.28776" lon="-71.06544"/> 
<point lat="42.28618" lon="-71.06448"/> 
<point lat="42.2858" lon="-71.06439"/> 
<point lat="42.28571" lon="-71.0643"/> 
<point lat="42.28465" lon="-71.06449"/> 
</path> 
<path> 
<point lat="42.27864" lon="-71.07972"/> 
<point lat="42.2787099" lon="-71.07968"/> 
<point lat="42.27847" lon="-71.078"/> 
<point lat="42.27828" lon="-71.0767599"/> 
<point lat="42.27808" lon="-71.07487"/> 
<point lat="42.27804" lon="-71.07317"/> 
<point lat="42.27802" lon="-71.07257"/> 
<point lat="42.2783" lon="-71.07102"/> 
<point lat="42.27881" lon="-71.0695099"/> 
<point lat="42.27896" lon="-71.06953"/> 
<point lat="42.28007" lon="-71.07021"/> 
<point lat="42.28117" lon="-71.0708499"/> 
<point lat="42.28127" lon="-71.07096"/> 
<point lat="42.28192" lon="-71.07117"/> 
<point lat="42.2819999" lon="-71.07127"/> 
<point lat="42.28344" lon="-71.0714"/> 
</path> 
<path> 
<point lat="42.28465" lon="-71.06449"/> 
<point lat="42.28475" lon="-71.06444"/> 
<point lat="42.28489" lon="-71.06453"/> 
<point lat="42.28571" lon="-71.0643"/> 
<point lat="42.28589" lon="-71.0643"/> 
<point lat="42.2874399" lon="-71.06511"/> 
<point lat="42.28802" lon="-71.06551"/> 
<point lat="42.2884699" lon="-71.06608"/> 
<point lat="42.28904" lon="-71.06687"/> 
<point lat="42.28906" lon="-71.06701"/> 
<point lat="42.2895899" lon="-71.06819"/> 
<point lat="42.28967" lon="-71.06861"/> 
<point lat="42.29013" lon="-71.07078"/> 
<point lat="42.29019" lon="-71.07098"/> 
<point lat="42.2902" lon="-71.0716"/> 
<point lat="42.28942" lon="-71.0714"/> 
</path> 
<path> 
<point lat="42.28557" lon="-71.08038"/> 
<point lat="42.28523" lon="-71.08057"/> 
<point lat="42.28439" lon="-71.08092"/> 
<point lat="42.28429" lon="-71.08105"/> 
<point lat="42.28421" lon="-71.08136"/> 
<point lat="42.28353" lon="-71.08318"/> 
<point lat="42.28271" lon="-71.08527"/> 
<point lat="42.28229" lon="-71.08621"/> 
<point lat="42.28169" lon="-71.0869699"/> 
<point lat="42.28155" lon="-71.08705"/> 
<point lat="42.2812399" lon="-71.08654"/> 
<point lat="42.2811499" lon="-71.0863"/> 
<point lat="42.28078" lon="-71.08462"/> 
<point lat="42.28079" lon="-71.08448"/> 
<point lat="42.28041" lon="-71.0828499"/> 
<point lat="42.28042" lon="-71.08265"/> 
<point lat="42.28035" lon="-71.08249"/> 
<point lat="42.2792699" lon="-71.08096"/> 
<point lat="42.27884" lon="-71.08015"/> 
<point lat="42.27864" lon="-71.07972"/> 
</path> 
<path> 
<point lat="42.28735" lon="-71.07129"/> 
<point lat="42.2866799" lon="-71.07117"/> 
<point lat="42.28543" lon="-71.07123"/> 
</path> 
<path> 
<point lat="42.27851" lon="-71.07051"/> 
<point lat="42.2781" lon="-71.07222"/> 
<point lat="42.27813" lon="-71.07243"/> 
<point lat="42.27805" lon="-71.0737"/> 
<point lat="42.27819" lon="-71.07492"/> 
<point lat="42.27839" lon="-71.07682"/> 
<point lat="42.27847" lon="-71.078"/> 
<point lat="42.27864" lon="-71.07937"/> 
<point lat="42.27874" lon="-71.0797599"/> 
<point lat="42.27884" lon="-71.08015"/> 
<point lat="42.27938" lon="-71.08094"/> 
<point lat="42.2801199" lon="-71.08213"/> 
<point lat="42.28036" lon="-71.08239"/> 
<point lat="42.28042" lon="-71.08265"/> 
<point lat="42.28089" lon="-71.08466"/> 
</path> 
<path> 
<point lat="42.28219" lon="-71.08625"/> 
<point lat="42.28229" lon="-71.08621"/> 
<point lat="42.28348" lon="-71.08305"/> 
<point lat="42.2842" lon="-71.08126"/> 
<point lat="42.28416" lon="-71.08123"/> 
<point lat="42.2842399" lon="-71.0811499"/> 
<point lat="42.28439" lon="-71.08092"/> 
<point lat="42.28536" lon="-71.0804"/> 
<point lat="42.28539" lon="-71.08046"/> 
<point lat="42.28622" lon="-71.07959"/> 
<point lat="42.28721" lon="-71.0786399"/> 
<point lat="42.2877" lon="-71.0782"/> 
<point lat="42.2879099" lon="-71.0779"/> 
<point lat="42.28798" lon="-71.07781"/> 
<point lat="42.28822" lon="-71.0766"/> 
</path> 
<path> 
<point lat="42.28942" lon="-71.0714"/> 
<point lat="42.28872" lon="-71.0711199"/> 
<point lat="42.28804" lon="-71.07116"/> 
<point lat="42.28804" lon="-71.07122"/> 
<point lat="42.28735" lon="-71.07129"/> 
</path> 
<path> 
<point lat="42.28344" lon="-71.0714"/> 
<point lat="42.28399" lon="-71.07157"/> 
<point lat="42.28448" lon="-71.07154"/> 
<point lat="42.2846199" lon="-71.07143"/> 
</path> 
<path> 
<point lat="42.28822" lon="-71.0766"/> 
<point lat="42.28826" lon="-71.07661"/> 
<point lat="42.2884" lon="-71.07603"/> 
<point lat="42.28871" lon="-71.07531"/> 
<point lat="42.28878" lon="-71.07484"/> 
<point lat="42.2890299" lon="-71.07389"/> 
<point lat="42.28917" lon="-71.07313"/> 
</path> 
<path> 
<point lat="42.28543" lon="-71.07123"/> 
<point lat="42.28533" lon="-71.07118"/> 
<point lat="42.28459" lon="-71.07157"/> 
<point lat="42.28433" lon="-71.07157"/> 
<point lat="42.28353" lon="-71.0714799"/> 
<point lat="42.28317" lon="-71.0714799"/> 
</path> 
<path> 
<point lat="42.28807" lon="-71.07776"/> 
<point lat="42.28787" lon="-71.07799"/> 
<point lat="42.28721" lon="-71.07879"/> 
<point lat="42.28711" lon="-71.07886"/> 
<point lat="42.28642" lon="-71.07955"/> 
<point lat="42.28557" lon="-71.08038"/> 
</path> 
<path> 
<point lat="42.28317" lon="-71.0714799"/> 
<point lat="42.28254" lon="-71.07135"/> 
<point lat="42.28208" lon="-71.07135"/> 
<point lat="42.2819999" lon="-71.07127"/> 
<point lat="42.28132" lon="-71.07104"/> 
<point lat="42.28018" lon="-71.07035"/> 
<point lat="42.27998" lon="-71.07029"/> 
<point lat="42.27881" lon="-71.0695099"/> 
<point lat="42.27851" lon="-71.07051"/> 
</path> 
<path> 
<point lat="42.28935" lon="-71.0729999"/> 
<point lat="42.28926" lon="-71.07306"/> 
<point lat="42.28884" lon="-71.07474"/> 
<point lat="42.28866" lon="-71.07545"/> 
<point lat="42.2887" lon="-71.07548"/> 
</path> 
<path> 
<point lat="42.28465" lon="-71.06449"/> 
<point lat="42.28475" lon="-71.06444"/> 
<point lat="42.28489" lon="-71.06453"/> 
<point lat="42.28571" lon="-71.0643"/> 
<point lat="42.28589" lon="-71.0643"/> 
<point lat="42.2874399" lon="-71.06511"/> 
<point lat="42.28802" lon="-71.06551"/> 
<point lat="42.2884699" lon="-71.06608"/> 
<point lat="42.28904" lon="-71.06687"/> 
<point lat="42.28906" lon="-71.06701"/> 
<point lat="42.2895899" lon="-71.06819"/> 
<point lat="42.28967" lon="-71.06861"/> 
<point lat="42.29013" lon="-71.07078"/> 
<point lat="42.29019" lon="-71.07098"/> 
<point lat="42.2902" lon="-71.072"/> 
<point lat="42.28944" lon="-71.0728"/> 
<point lat="42.28934" lon="-71.07292"/> 
<point lat="42.28935" lon="-71.0729999"/> 
</path> 
<path> 
<point lat="42.2887" lon="-71.07548"/> 
<point lat="42.28833" lon="-71.0762699"/> 
<point lat="42.28801" lon="-71.07772"/> 
<point lat="42.28807" lon="-71.07776"/> 
</path> 
</route> 
</body> 
"""
        for ordering in permutations(params.items()):
            url = nextbus.RPC_URL + url_params(ordering)
            responses[url] = response     

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