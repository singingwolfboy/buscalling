from buscall.models.user import User
from buscall.models.listener import BusListener
from buscall.models.nextbus import Agency, Route, Direction, Stop
from tests.util import CustomTestCase
from ndb import Key

class NewListenerFormTest(CustomTestCase):
    def test_create_recurring_listener(self):
        self.login("bob@gmail.com")
        self.app.post("/listeners/new", data={
            "agency_id": "mbta",
            "route_id": "556",
            "direction_id": "n",
            "stop_id": "123",
            "start": "06:16:00",
            "recur": "y",
            "mon": "y",
            "thu": "y",
        })
        user = User.create_from_email("bob@gmail.com")
        user_key = user.put()
        listener = BusListener.query(
                BusListener.user_key == user_key,
                BusListener.agency_key == Key(Agency, "mbta"),
                BusListener.route_key == Key(Route, "mbta|556"),
                BusListener.direction_key == Key(Direction, "mbta|556|n"),
                BusListener.stop_key == Key(Stop, "mbta|556|n|123"),
            ).get()
        # assert listener is not None
        # assert listener.agency.id == "mbta"
        # assert listener.route.id == "556"
