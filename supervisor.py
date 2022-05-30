from flask import Flask, request, render_template, jsonify
import socket
from threading import Thread
from utils.common_utils import *
from utils.supervisor_utils import *
from utils.html_generator import generate_tree
from utils.tree_manager import *

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
rootConnection = False
index_last_broker_sent = 0
supervisor_id = None
root_id = None


@app.errorhandler(Exception)
def handle_exceptions(exc):
    if not exc.args or len(exc.args) < 2:
        return 'Error', 500

    return exc.args[0], exc.args[1]


@app.route("/tree", methods=['GET'])
def html_tree():
    file_name = generate_tree(get_tree(), root_id)
    return render_template(f"{file_name}.html")


@app.route("/jtree", methods=['GET'])
def get_jtree():
    tree = get_tree()
    tree_info = {len(tree): tree}
    return jsonify(tree_info)


@app.route("/node/register", methods=['POST'])
def register_node():
    node_ip, node_port = get_register_node_info(request.json)
    node_id = get_node_id(node_ip, node_port)
    if not rootConnection:  # No root tree is present
        father_id = supervisor_id
    elif is_node_in_tree(node_id):
        # remove son from father
        old_father = remove_father_from_node_if_present(node_id)
        # search new father
        father_id = search_father_and_add_as_son(node_id, supervisor_id, old_father)
    else:
        father_id = search_father_and_add_as_son(node_id, supervisor_id)
    return father_id, 200


@app.route("/node/confirm", methods=['POST'])
def confirm_node():
    father_node_ip, father_node_port, son_node_ip, son_node_port = get_confirm_node_info(request.json)
    father_id = get_node_id(father_node_ip, father_node_port)
    son_id = get_node_id(son_node_ip, son_node_port)
    if not is_node_in_tree(father_id):
        raise Exception("Father node not found", 12163)  # 12163 http disconnected, father must reconnect to network

    if not is_son_of(father_id, son_id):
        raise Exception('Son not found', 404)

    if get_node_status(father_id, son_id) == Status.CONFIRMED:
        return 'Already confirmed', 200

    confirm_son_and_add_as_node(father_id, son_id)
    remove_sons_if_needed(father_id)
    return 'Success', 200


@app.route("/node/down", methods=['POST'])
def node_down():
    reporter_node_id, down_node_id = get_down_node_info(request.json)
    if reporter_node_id not in tree_TO_CHANGE:
        raise Exception('Bad request', 400)

    reporter_node = tree_TO_CHANGE[reporter_node_id]
    is_father_for_reporter = is_father_for_node(reporter_node, down_node_id)
    if not is_father_for_reporter and not is_son_for_node(reporter_node, down_node_id):
        raise Exception(f"Relationship not found between nodes: {reporter_node_id} - {down_node_id}", 404)
    if is_father_for_reporter and is_son_for_node(reporter_node, down_node_id):
        raise Exception(
            f"Double Relationship found between nodes: {reporter_node_id} - {down_node_id}. Needs more investigation",
            500)

    # remove link from the reporter
    if is_father_for_reporter:
        reporter_node[FATHER] = None
    else:
        del reporter_node[SONS][down_node_id]
        reporter_node[IS_FULL] = False

    # remove the link from the down node
    if down_node_id in tree_TO_CHANGE:
        down_node = tree_TO_CHANGE[down_node_id]
        if is_father_for_reporter and is_son_for_node(down_node, reporter_node_id):
            del down_node[SONS][reporter_node_id]
            down_node[IS_FULL] = False
        elif not is_father_for_reporter and is_father_for_node(down_node, reporter_node_id):
            down_node[FATHER] = None

        # if the down node has not active connections then remove it from tree_TO_CHANGE structure
        if down_node[FATHER] is None and len(down_node[SONS]) == 0:
            remove_node(tree_TO_CHANGE, down_node_id)
    return "Success", 200


@app.route("/broker", methods=['GET'])
def get_available_broker():
    global index_last_broker_sent
    node_ids = list(n_id for n_id in tree_TO_CHANGE if tree_TO_CHANGE[n_id][FATHER])
    if len(node_ids) == 0:
        raise Exception("No available broker!", 404)

    if index_last_broker_sent >= len(node_ids):
        index_last_broker_sent = 0

    broker_id = node_ids[index_last_broker_sent]
    index_last_broker_sent += 1
    return broker_id, 200


def root_manager(conn, address):
    global rootConnection, tree_TO_CHANGE, root_id
    while not rootConnection:
        print("Waiting root node port")
        conn.sendall(build_command(Command.RESULT, 'OK'))
        data = conn.recv(1024)
        if not data:
            print(f'root connection closed before confirmed!')
            break
        try:
            command, port = get_command_and_value(data)
            if command != Command.PORT or port < LOWER_AVAILABLE_PORT or port > UPPER_AVAILABLE_PORT:
                conn.sendall(build_command(Command.RESULT, 'ERROR'))
                print(f"Error decoding port command and value")
                continue
            rootConnection = True
            root_id = f'{address[0]}:{port}'
            if root_id in tree_TO_CHANGE:
                tree_TO_CHANGE[root_id][FATHER] = supervisor_id
            else:
                temp_tree_TO_CHANGE = create_node(root_id, supervisor_id)
                temp_tree_TO_CHANGE.update(tree_TO_CHANGE)
                tree_TO_CHANGE = temp_tree_TO_CHANGE
            conn.sendall(build_command(Command.RESULT, 'OK'))
            print(f'root connected!: {address}. Root id: {root_id}')
        except Exception as e:
            print(f'From {address}: {data}. {e}')

    while rootConnection:
        data = conn.recv(1024)
        if not data:
            print(f'root connection closed!')
            # for son in tree_TO_CHANGE[root_id][SONS]:
            #     remove_father(tree_TO_CHANGE[son])
            # remove_node(tree_TO_CHANGE, root_id)
            tree_TO_CHANGE[root_id][FATHER] = None
            if len(tree_TO_CHANGE) == 1:
                del tree_TO_CHANGE[root_id]
            rootConnection = False
        else:
            print(data)


def root_connection_manager(server_port):
    global TCPServerSocket
    TCPServerSocket.bind(('0.0.0.0', server_port))
    print(f"Supervisor socket listening on port: {server_port}")
    while True:
        print('waiting for new root...')
        TCPServerSocket.listen()
        conn, address = TCPServerSocket.accept()
        if not rootConnection:
            Thread(target=root_manager, args=(conn, address)).start()
        else:
            conn.sendall(build_command(Command.RESULT, 'ERROR - Root already in tree_TO_CHANGE.'))


if __name__ == '__main__':
    args = supervisor_initialize_parser()
    tcp_server_port = args.socket_port
    supervisor_id = f'{get_host_address()}:{tcp_server_port}'
    Thread(target=root_connection_manager, args=(tcp_server_port,)).start()
    app.run(port=args.flask_port, host='0.0.0.0')
