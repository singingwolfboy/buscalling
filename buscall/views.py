from buscall import app
from flask import render_template
from google.appengine.api import urlfetch
from xml.dom.minidom import parseString
import xpath

@app.route('/')
def hello():
    return render_template('hello.html')

RPC_URL = "http://webservices.nextbus.com/service/publicXMLFeed?a=mbta"

@app.route('/list')
def route_list():
    "Asynchronously fetch the list of supported MBTA routes."
    rpc = urlfetch.create_rpc()
    url = RPC_URL + "&command=routeList"
    urlfetch.make_fetch_call(rpc, url)
    # Here we could do things asynchronously, but in this case, 
    # we need the result of the RPC before we can do anything else.
    try:
        result = rpc.get_result()
        if result.status_code == 200:
            xmldoc = parseString(result.content)
            routes = xpath.find("//body/route", xmldoc)
            return render_template('route_list.html', routes=routes)
            
    except urlfetch.DownloadError:
        return "Download error: " + url
    
