from buscall import app
import datetime

#if app.debug:
if True:
    # sandbox info
    sandbox = True
    url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
    pdt_token = "VXASrbamQDoW0olGqyfA7Ty-HdawXzNfCfvbGQ_83Dv1Ecle4PF7Wpe8oP0"
    subscribe_button_id = "GUUGPYAWQ63CG"
    unsubscribe_button_id = "BPQAK7D34287Q"
else:
    # real info
    sandbox = False
    url = "https://www.paypal.com/cgi-bin/webscr"
    pdt_token = "SWCM2tf41PckuxT-MNYirYukaWXdkTS9kWIqmSNMDKrGzXHstbhO8RGZ5pu"
    subscribe_button_id = "W42Q7VA9H8USQ"
    unsubscribe_button_id = "WYWXRN23UG45Q"

def parse_paypal_date(date_str):
    return datetime.datetime.strptime(date_str, "%H:%M:%S %b %d, %Y PDT")