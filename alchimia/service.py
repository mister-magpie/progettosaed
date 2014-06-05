##spyne-flask webservice
#prende in input gli url dei wsdl dei negozi e poi li quera uno per volta per ottenere i risultati
from flask import Flask
from flask.ext.spyne import Spyne
from spyne.protocol.soap import Soap11
from spyne.model.primitive import Unicode, Integer
from spyne.model.complex import Iterable, ComplexModel

import logging
h = logging.StreamHandler()
rl = logging.getLogger()
rl.setLevel(logging.DEBUG)
rl.addHandler(h)

app = Flask(__name__)
spyne = Spyne(app)

shops = {"negozio1": "http://localhost:8000/?wsdl"}

class RegisterService(spyne.Service):
    __service_url_path__ = '/soap/registrationservice'
    __in_protocol__ = Soap11(validator='lxml')
    __out_protocol__ = Soap11()
    """
    this service generates a dictonary of registered shop which shall be queried for results
    """
    @spyne.srpc(Unicode, Unicode, _returns=Integer)
    def register_shop(shop_name, shop_url):
    	shops[shop_name] = shop_url
    	return 1

#TODO
"""
a function which connects to each shop in the dict and retrives albums throught their web service


from suds.client import Client as SudsClient
def clientSOAP(args):
    srv_url = 'http://127.0.0.1:8000/?wsdl'
    client = SudsClient(url=url, cache=None)
    client.service.someservice()

"""

#####################
#PRETTY HOMEPAGE PART YAY
######################
@app.route('/cane')
def cane():
	shops['negozio2'] = "http://localhost:8002/?wsdl"
	s = ""
	for i in shops:
		s += "<p>" + i +"\t"+ shops[i] + "</p>"
	return s

if __name__ == '__main__':
	app.debug = True
	app.run(port = 5000)