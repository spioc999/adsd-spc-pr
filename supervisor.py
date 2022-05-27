from flask import Flask, request, jsonify, render_template
import socket
from threading import Thread
from utils.common_utils import *
from utils.supervisor_utils import *

app = Flask(__name__)
app.config['JSON_SORT_KEYS'] = False
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
tree = dict()
rootConnection = False


@app.route("/tree")
def get_tree():
    return render_template("tree.html")


@app.route("/node/register", methods=['POST'])
def register_node():
    try:
        node_ip, node_port = getRegisterNodeInfo(request.json)
        node_id = f'{node_ip}:{node_port}'
        if not rootConnection:  # No root tree is present
            # sent enums tcp server socket to root
            father_id = f'{get_host_address()}:{tcp_server_port}'
        elif node_id in tree:
            # get father id
            current_father_id = tree[node_id][FATHER]
            # remove son from father
            if current_father_id:
                remove_son(tree[current_father_id], node_id)
            # search new father
            father_id = search_father_and_add_as_son(tree, node_id, current_father_id)
        else:
            father_id = search_father_and_add_as_son(tree, node_id)
        return father_id, 200
    except Exception as exc:
        if not exc.args or len(exc.args) < 2:
            return 'Error', 500

        return exc.args[0], exc.args[1]


@app.route("/node/confirm", methods=['POST'])
def confirm_node():
    try:
        father_node_ip, father_node_port, son_node_ip, son_node_port = getConfirmNodeInfo(request.json)
        father_node_id = f'{father_node_ip}:{father_node_port}'
        son_node_id = f'{son_node_ip}:{son_node_port}'
        father_node = tree[father_node_id]
        if father_node is None:
            raise Exception('Father to register', 404)  # TODO say to father to connect

        son_dict_item = father_node[SONS][son_node_id]
        if son_dict_item is None:
            raise Exception('Son not found', 404)  # TODO father must refuse son connection
        elif son_dict_item[STATUS] == Status.CONFIRMED:
            return 'Already confirmed', 200

        son_dict_item[STATUS] = Status.CONFIRMED
        son_dict_item[TIME] = datetime.now()
        new_node = create_node(son_node_id, father_node_id)
        tree.update(new_node)
        remove_sons_if_needed(father_node)
        return 'Success', 200
    except Exception as exc:
        if not exc.args or len(exc.args) < 2:
            return 'Error', 500

        return exc.args[0], exc.args[1]


@app.route("/node/down", methods=['POST'])
def down_node():
    reporter_ip, reporter_port, down_node_id = get_down_node_info(request.json)
    # look if the down node is a father or a son
    # remove it link with the reporter
    # remove the link from the down node to the reporter
    # if the down node has not active connections then remove it from tree structure


def root_connection_manager(server_port):
    global rootConnection
    global TCPServerSocket
    global tree
    TCPServerSocket.bind(('0.0.0.0', server_port))
    print(f"Supervisor socket listening on port: {server_port}")
    root_id = None
    while True:
        print('waiting for new root...')
        TCPServerSocket.listen()
        conn, address = TCPServerSocket.accept()
        while not rootConnection:
            print("Waiting root node port")
            data = conn.recv(1024)
            if not data:
                print(f'root connection closed before confirmed!')
                break
            try:
                command, port = get_command_and_value(data)
                if command != Command.PORT or port < 49152 or port > 65535:
                    conn.sendall(build_command(Command.RESULT, 'ERROR'))
                    print(f"Error decoding port command and value")
                    continue
                rootConnection = True
                root_id = f'{address[0]}:{port}'
                temp_tree = create_node(root_id, f'{get_host_address()}:{server_port}')
                if len(tree) > 0:
                    temp_tree.update(tree)
                tree = temp_tree
                conn.sendall(build_command(Command.RESULT, 'OK'))
                print(f'root connected!: {address}. Root id: {root_id}')
            except Exception as e:
                print(f'From {address}: {data}. {e}')

        while rootConnection:
            data = conn.recv(1024)
            if not data:
                print(f'root connection closed!')
                for son in tree[root_id][SONS]:
                    remove_father(tree[son])
                remove_node(tree, root_id)
                rootConnection = False
            else:
                print(data)


if __name__ == '__main__':
    args = supervisor_initialize_parser()
    tcp_server_port = args.socket_port
    Thread(target=root_connection_manager, args=(tcp_server_port,)).start()
    app.run(port=args.flask_port, host='0.0.0.0')

# TODO confirm each node when it sends to father the port in which TCP server is available
