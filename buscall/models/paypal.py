from buscall import app
import datetime
from decimal import Decimal
try:
    from collections import namedtuple
except ImportError:
    from collections_backport import namedtuple

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

# build mapping of paypal item ID to price and number of credits
Item = namedtuple("Item", ["price", "credits"])
item_map = {
    1: Item(price=Decimal("0.99"), credits=1),
    6: Item(price=Decimal("5.00"), credits=6),
}

def parse_paypal_date(date_str):
    return datetime.datetime.strptime(date_str, "%H:%M:%S %b %d, %Y PDT")
