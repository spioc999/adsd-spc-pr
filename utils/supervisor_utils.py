import argparse
from utils.tree_manager import *


def get_register_node_info(json):
    if json and all(key in json.keys() for key in [NODE_IP, NODE_PORT]):
        return json[NODE_IP], json[NODE_PORT]
    raise Exception('Bad request', 400)


def get_confirm_node_info(json):
    if json and all(key in json.keys() for key in [FATHER, SON]):
        father = json[FATHER]
        son = json[SON]

        if all(key in father.keys() for key in [NODE_IP, NODE_PORT]) and all(key in son.keys() for key in [NODE_IP, NODE_PORT]):
            return father[NODE_IP], father[NODE_PORT], son[NODE_IP], son[NODE_PORT]
        
    raise Exception('Bad request', 400)


def get_down_node_info(json):
    if json and all(key in json.keys() for key in [NODE_ID, DOWN_ID]):
        return json[NODE_ID], json[DOWN_ID]
    raise Exception('Bad request', 400)


def search_father_and_add_as_son(node_id, supervisor_id, father_to_exclude=None, unlimited_branch_size=False):
    if father_to_exclude and father_to_exclude == supervisor_id:  # TODO: not clear check
        raise Exception("No available fathers", 409)  # http conflict

    for tree_node_id in get_tree():
        if tree_node_id != father_to_exclude and tree_node_id != node_id and (unlimited_branch_size or not is_full(tree_node_id)) and has_father(tree_node_id):
            error, is_sub_node = is_target_a_sub_node(node_id, tree_node_id, supervisor_id)
            if not error and not is_sub_node:
                add_son(tree_node_id, node_id, unlimited_branch_size)
                return tree_node_id
    return search_father_and_add_as_son(node_id, supervisor_id, father_to_exclude=father_to_exclude, unlimited_branch_size=True)  # If not available father extend branch size


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
