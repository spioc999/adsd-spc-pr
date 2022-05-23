from netifaces import interfaces, ifaddresses, AF_INET
FATHER = "father"
SONS = "sons"
NODE_IP = "node_ip"
NODE_PORT = "node_port"
STATUS = "status"
TIME = "time"
TREE_BRANCH_SIZE = 2 #Binary tree
SON = "son"
host_address = None

def getRegisterNodeInfo(json):
    if json and all(key in json.keys() for key in [NODE_IP, NODE_PORT]):
        return json[NODE_IP], json[NODE_PORT]
    
    raise Exception('Bad request', 400)


def getConfirmNodeInfo(json):
    if json and all(key in json.keys() for key in [FATHER, SON]):

        father = json[FATHER]
        son = json[SON]

        if all(key in father.keys() for key in [NODE_IP, NODE_PORT]) and all(key in son.keys() for key in [NODE_IP, NODE_PORT]):
            return father[NODE_IP], father[NODE_PORT], son[NODE_IP], son[NODE_PORT]
        
    raise Exception('Bad request', 400)


def get_host_address():
    for ifaceName in interfaces():
        addresses = ' '.join([i['addr'] for i in ifaddresses(ifaceName).setdefault(AF_INET, [{'addr':''}] )])
        if addresses != '' and addresses != '0.0.0.0' and addresses != '127.0.0.1':
            return addresses
    return '127.0.0.1'
