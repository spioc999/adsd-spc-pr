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
supervisor_id = None
root_id = None
root_connection_lock = Lock()


@app.errorhandler(Exception)
def handle_exceptions(exc):
    print(f"Raised exception: {exc}")
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
        old_father = remove_node_from_father_if_present(node_id)
        # search new father
        father_id = search_father_and_add_as_son(node_id, supervisor_id, old_father)
    else:
        father_id = search_father_and_add_as_son(node_id, supervisor_id)
    print(f"Next father of {node_id} : {father_id}")
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
    if not is_node_in_tree(reporter_node_id):
        raise Exception('Bad request', 400)

    # down_node must be father or son
    down_node_is_father = is_father_for_node(reporter_node_id, down_node_id)
    down_node_is_son = is_son_of(reporter_node_id, down_node_id)

    if not down_node_is_father and not down_node_is_son:
        raise Exception(f"Relationship not found between nodes: {reporter_node_id} - {down_node_id}", 404)
    if down_node_is_father and down_node_is_son:
        raise Exception(f"Double Relationship found between nodes: {reporter_node_id} - {down_node_id}. Needs more investigation", 500)

    # remove link from the reporter
    if down_node_is_son:
        remove_son(reporter_node_id, down_node_id)
    else:
        remove_father(reporter_node_id)

    # remove the link from the down node
    if is_node_in_tree(down_node_id):
        if down_node_is_son:
            remove_father(down_node_id)
        elif down_node_is_father:
            remove_son(down_node_id, reporter_node_id)
        # if the down node has not active connections then remove it from tree_TO_CHANGE structure
        if is_alone(down_node_id):
            remove_node(down_node_id)
    return "Success", 200


@app.route("/broker", methods=['GET'])
def get_available_broker():
    return get_next_broker(), 200


def root_manager(conn, address):
    global rootConnection, root_id
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
            if not get_root_connection_value():
                set_root_connection_value(True)
            else:
                conn.sendall(build_command(Command.RESULT, 'ERROR - Root already in tree.'))
                raise RuntimeError("Root leadership conflict", 500)
            root_id = get_node_id(address[0], port)
            if is_node_in_tree(root_id):
                add_father(root_id, supervisor_id)
            else:
                add_root_node(root_id, supervisor_id)
            conn.sendall(build_command(Command.RESULT, 'OK'))
            print(f'root connected!: {address}. Root id: {root_id}\n')
        except Exception as e:
            print(f'From {address}: {data}. {e}')

    while rootConnection:
        data = conn.recv(1024)
        if not data:
            print(f'root connection closed!')
            remove_father(root_id)
            if len(get_tree()) == 1 or is_alone(root_id):
                remove_node(root_id)
            set_root_connection_value(False)
        else:
            print(data)


def root_connection_manager(server_port):
    global TCPServerSocket, supervisor_id
    try:
        TCPServerSocket.bind(('0.0.0.0', server_port))
    except OSError as error:
        print(f"Error {error}")
        server_port += 1
    supervisor_id = get_node_id(get_host_address(), tcp_server_port)
    print(f"Supervisor socket listening on port: {server_port}")
    while True:
        TCPServerSocket.listen()
        conn, address = TCPServerSocket.accept()
        if not get_root_connection_value():
            print('A new root is trying to connect')
            Thread(target=root_manager, args=(conn, address)).start()
        else:
            conn.sendall(build_command(Command.RESULT, 'ERROR - Root already in tree.'))


def set_root_connection_value(value):
    global rootConnection
    root_connection_lock.acquire()
    rootConnection = value
    root_connection_lock.release()


def get_root_connection_value():
    root_connection_lock.acquire()
    current_value = rootConnection
    root_connection_lock.release()
    return current_value


if __name__ == '__main__':
    args = supervisor_initialize_parser()
    tcp_server_port = args.socket_port
    Thread(target=root_connection_manager, args=(tcp_server_port,)).start()
    app.run(port=args.flask_port, host='0.0.0.0')
