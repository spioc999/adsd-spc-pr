from flask import Flask, request, jsonify
from SupervisorUtils import *
from Status import Status
import socket
from threading import Thread
from datetime import datetime

FLASK_PORT = 10000
TCP_SERVER_PORT = 10001
app = Flask(__name__)
TCPServerSocket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
tree = dict()
rootConnection = False

@app.route("/tree", methods=['GET'])
def getTree():
    return jsonify(tree)


@app.route("/node/register", methods=['POST'])
def registerNode():
    try:
        node_ip, node_port = getRegisterNodeInfo(request.json)
        node_id = f'{node_ip}:{node_port}'
        if not rootConnection:  # No root tree is present
            #sent supervisor tcp server socket to root
            father_id = f'{get_host_address()}:{TCP_SERVER_PORT}'
        elif node_id in tree:
            # get father id
            current_father_id = tree[node_id][FATHER]
            # remove son from father
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
def confirmNode():
    try:
        father_node_ip, father_node_port, son_node_ip, son_node_port = getConfirmNodeInfo(request.json)
        father_node_id = f'{father_node_ip}:{father_node_port}'
        son_node_id = f'{son_node_ip}:{son_node_port}'
        father_node = tree[father_node_id]
        if father_node is None:
            raise Exception('Father to register', 404) #TODO say to father to connect
        
        son_dict_item = father_node[SONS][son_node_id]
        if son_dict_item is None:
            raise Exception('Son not found', 404) #TODO father must refuse son connection
        elif son_dict_item[STATUS] == Status.CONFIRMED:
            return 'Already confirmed', 200

        son_dict_item[STATUS] = Status.CONFIRMED
        son_dict_item[TIME] = datetime.now()
        add_node(tree, son_node_id, father_node_id)
        remove_sons_if_needed(father_node)
        return 'Success', 200
    except Exception as exc:
        if not exc.args or len(exc.args) < 2:
            return 'Error', 500
        
        return exc.args[0], exc.args[1]


def root_connection_manager(port):
    global rootConnection
    global TCPServerSocket
    TCPServerSocket.bind(('0.0.0.0', port))
    while True:
        print('waiting for new root...')
        TCPServerSocket.listen() 
        conn, addr = TCPServerSocket.accept()
        rootConnection = True
        root_id = f'{addr[0]}:{addr[1]}'
        add_node(tree, root_id, f'{get_host_address()}:{TCP_SERVER_PORT}')
        print(f'root connected!: {addr}')
        while True:
            data = conn.recv(1024)
            if not data:
                print(f'root connection closed!')
                for son in tree[root_id][SONS]:
                    remove_father(tree[son])
                remove_node(tree, root_id)
                rootConnection = False
                break
            else:
                print(data)


if __name__ == '__main__':
    Thread(target=root_connection_manager, args=(TCP_SERVER_PORT,)).start()
    app.run(port=FLASK_PORT, host='0.0.0.0')

#TODO confirm each node when it sends to father the port in which TCP server is available