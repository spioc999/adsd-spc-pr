from netifaces import interfaces, ifaddresses, AF_INET
from datetime import datetime
from Status import Status
FATHER = "father"
SONS = "sons"
NODE_IP = "node_ip"
NODE_PORT = "node_port"
STATUS = "status"
TIME = "time"
TREE_BRANCH_SIZE = 2 #Binary tree
SON = "son"
IS_FULL = "is_full"
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


def add_son(node, son_id, unlimited_branch_size=False):
    if unlimited_branch_size or len(node[SONS]) <= TREE_BRANCH_SIZE:
        node[SONS][son_id] = dict()
        node[SONS][son_id][STATUS] = Status.PENDING
        node[SONS][son_id][TIME] = datetime.now()
    else:
        raise RuntimeError(f"Too much sons for node with id:")


def remove_son(node, son_id):
    if node[IS_FULL]:
        node[IS_FULL] = False
    del node[SONS][son_id]


def remove_father(node):
    node[FATHER] = None


def search_father_and_add_son(tree, node_id, father_to_exclude=None, unlimited_branch_size=False):
    for node in tree:
        if node != father_to_exclude and node != node_id and (unlimited_branch_size or len(tree[node][SONS]) < TREE_BRANCH_SIZE) and not tree[node][IS_FULL]:
            father_id = node
            add_son(tree[node], node_id, unlimited_branch_size)
            return father_id
    return search_father_and_add_son(tree, node_id, unlimited_branch_size=True) # If not available father extend branch size


def remove_sons_if_needed(node):
    confirmed_sons = dict()
    sons = node[SONS]
    for son in sons:
        if sons[son][STATUS] == Status.CONFIRMED:
            confirmed_sons[son] = sons[son]

    if len(confirmed_sons) > TREE_BRANCH_SIZE:
        raise RuntimeError("Too much sons for node ")

    if len(confirmed_sons) == TREE_BRANCH_SIZE:
        node[SONS] = confirmed_sons
        node[IS_FULL] = True
        print(f"Dropping exceeded sons for node")


def add_node(tree, node_id, father_id):
    tree[node_id] = {
        FATHER: father_id,
        SONS: dict(),
        IS_FULL: False
    }


def remove_node(tree, node_id):
    del tree[node_id]