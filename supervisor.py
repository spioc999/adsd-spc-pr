from flask import Flask, request, jsonify
from SupervisorUtils import *
from Status import Status
from time import time

app = Flask(__name__)

tree = dict()


@app.route("/tree", methods=['GET'])
def getTree():
    return jsonify(tree)


@app.route("/node/register", methods=['POST'])
def registerNode():
    try:
        node_ip, node_port = getRegisterNodeInfo(request.json)
        node_id = f'{node_ip}:{node_port}'
        father_id = None
        if len(tree) == 0:
            tree[node_id] = {
                FATHER: None,
                SONS: dict()
            }
            return '', 200
        else:
            for node in tree:
                if len(tree[node][SONS]) < TREE_BRANCH_SIZE:
                    father_id = node
                    tree[node][SONS][node_id] = dict()
                    tree[node][SONS][node_id][STATUS] = Status.PENDING
                    tree[node][SONS][node_id][TIME] = time()
                    break
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
        son_dict_item[TIME] = time()
        tree[son_node_id] = {
            FATHER: father_node_id,
            SONS: dict()
        }

        return 'Success', 200
    except Exception as exc:
        if not exc.args or len(exc.args) < 2:
            return 'Error', 500
        
        return exc.args[0], exc.args[1]


if __name__ == '__main__':
    app.run(port=10000)
