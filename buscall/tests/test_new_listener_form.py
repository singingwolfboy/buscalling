from local_setup import ServiceTestCase
from google.appengine.api.users import User
from buscall.models.profile import UserProfile
from buscall.models.listener import BusListener

class NewListenerFormTest(ServiceTestCase):
    def test_create_recurring_listener(self):
        self.login("bob@gmail.com")
        self.app.post("/listeners/new", data={
            "agency_id": "mbta",
            "route_id": "556",
            #"direction_id": "n",
            "stop_id": "123",
            "start": "06:16:00",
            "recur": "y",
            "mon": "y",
            "thu": "y",
        })
        user = User("bob@gmail.com")
        profile = UserProfile.get_by_user(user)
        listener = BusListener.gql("WHERE profile = :profile AND agency_id = :agency_id AND "
            "route_id = :route_id AND stop_id = :stop_id", profile=profile, agency_id="mbta",
            route_id="556", stop_id="123")
        assert listener is not None