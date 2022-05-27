import argparse
from datetime import datetime
from enums.son_status import Status
import re
import random
import string
import os, shutil


FLASK_PORT = 10000
TCP_SERVER_PORT = 10001

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
regex_root_command = r"^\[PORT\]( {0,})([1-9]{1})([0-9]{3,})"


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


def get_down_node_info(json):
    pass


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


def decode_root_port_command(command): # TODO: Improve creting unique method to get command and value
    pattern = re.compile(regex_root_command)
    if pattern.match(command):
        return int(command.split(']')[1])
    raise ValueError("Command doesn't match the regex!")


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


HTML_HEADER = '<!DOCTYPE html>' \
              '<html lang="en">' \
              '<head><meta charset="UTF-8">' \
              '<link rel= "stylesheet" type= "text/css" href= "{{ url_for(\'static\',filename=\'styles/treeStyle.css\') }}">' \
             '</head><body><div class="tree">'
HTML_FOOTER = '</div></body></html>'
NODE_HTML_OPEN = "<li>"
NODE_HTML_CLOSE = "</li>"


def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str


def delete_file():
    folder = 'templates/'
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def get_html_node_structure(tree, node_id, status=''):
    status_html = f'<br/>{status}' if len(status) > 0 else ''
    tree_structure_html = NODE_HTML_OPEN + '<a>' + f'{node_id}{status_html}' + '</a>'
    if node_id in tree:
        if len(tree[node_id][SONS]) > 0:
            tree_structure_html += "<ul>"
        for son_id in tree[node_id][SONS]:
            status_son = tree[node_id][SONS][son_id][STATUS]
            tree_structure_html += get_html_node_structure(tree, son_id, status_son)
        if len(tree[node_id][SONS]) > 0:
            tree_structure_html += "</ul>"
    tree_structure_html += NODE_HTML_CLOSE
    return tree_structure_html


def generate_tree(tree):
    os.makedirs(os.path.dirname('templates/'), exist_ok=True)
    delete_file()
    temp_file_name = get_random_string(8)
    tree_page = HTML_HEADER + ('<ul>' + get_html_node_structure(tree, list(tree.keys())[0]) + '</ul>' if len(tree.keys()) > 0 else '<p> Empty Tree </p>') + HTML_FOOTER
    tree_html = open(f"templates/{temp_file_name}.html", "w+")
    tree_html.write(tree_page)
    tree_html.close()
    return temp_file_name

