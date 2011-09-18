from buscall import app
import datetime

if app.debug:
    # sandbox info
    sandbox = True
    url = "https://www.sandbox.paypal.com/cgi-bin/webscr"
    pdt_token = "VXASrbamQDoW0olGqyfA7Ty-HdawXzNfCfvbGQ_83Dv1Ecle4PF7Wpe8oP0"
    button_id = dict(
        subscribe   = "GUUGPYAWQ63CG",
        unsubscribe = "BPQAK7D34287Q",
        pickups_1   = "PTDH2YFRJQE38",
    )
    subscribe_button_id = "GUUGPYAWQ63CG"
    unsubscribe_button_id = "BPQAK7D34287Q"
else:
    # real info
    sandbox = False
    url = "https://www.paypal.com/cgi-bin/webscr"
    pdt_token = "SWCM2tf41PckuxT-MNYirYukaWXdkTS9kWIqmSNMDKrGzXHstbhO8RGZ5pu"
    button_id = dict(
        subscribe   = "W42Q7VA9H8USQ",
        unsubscribe = "WYWXRN23UG45Q",
        pickups_1   = "K5PVGSXFYV6L8",
    )

def parse_paypal_date(date_str):
    return datetime.datetime.strptime(date_str, "%H:%M:%S %b %d, %Y PDT")