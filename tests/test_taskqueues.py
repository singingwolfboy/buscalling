from tests.util import CustomTestCase
import simplejson as json
from buscall.models import Agency, Route

class TaskQueueTestCase(CustomTestCase):
    def test_add_queues(self):
        rv = self.app.post("/tasks/nextbus/update")
        taskqueue_stub = self.testbed.get_stub('taskqueue')
        tasks = taskqueue_stub.GetTasks('default')
        assert len(tasks) == 32
        resp = json.loads(rv.data)
        assert len(resp['agencies']) == 32
