from Status import Status

class Node:

    def __init__(self, node_ip, node_port):
        self.node_id = f'{node_ip}:{node_port}'
        self.node_ip = node_ip
        self.node_port = node_port
        self.status = Status.PENDING
