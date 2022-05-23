from Status import Status
from time import time
import json

class Node:

    def __init__(self, node_ip, node_port):
        self.node_id = f'{node_ip}:{node_port}'
        self.status = Status.PENDING
        #self.updateTimestamp = time()

    def toJSON(self):
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=4)
