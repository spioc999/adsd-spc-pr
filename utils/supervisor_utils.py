import argparse
from datetime import datetime
from enums.son_status import Status
from constants import *

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


def getDownNodeInfo(json):
    if json and all(key in json.jeys() for key in [NODE_ID, DOWN_ID, IS_FATHER]):
        return json[NODE_ID], json[DOWN_ID], json[IS_FATHER]
    raise Exception('Bad request', 400)


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


def search_father_and_add_as_son(tree, node_id, father_to_exclude=None, unlimited_branch_size=False):
    for node in tree:
        if node != father_to_exclude and node != node_id and (unlimited_branch_size or len(tree[node][SONS]) < TREE_BRANCH_SIZE) and not tree[node][IS_FULL] and tree[node][FATHER]:
            father_id = node
            add_son(tree[node], node_id, unlimited_branch_size)
            return father_id
    return search_father_and_add_as_son(tree, node_id, unlimited_branch_size=True)  # If not available father extend branch size


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


def create_node(node_id, father_id):
    return {
            node_id: {
                FATHER: father_id,
                SONS: dict(),
                IS_FULL: False
            }
        }


def remove_node(tree, node_id):
    del tree[node_id]


def supervisor_initialize_parser():
    """Utility method that initializes argparse and return the args
        @rtype: Namespace object
        @returns: object built up from attributes parsed out of the command line
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--socket_port",
                        help="Port number that will be assigned to enums's socket",
                        required=False,
                        type=int,
                        default=TCP_SERVER_PORT)
    parser.add_argument("-fp", "--flask_port",
                        help="Port number that will be assigned to flask's server",
                        type=int,
                        required=False,
                        default=FLASK_PORT)
    return parser.parse_args()

