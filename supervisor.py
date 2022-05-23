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
    return father_id, 200


if __name__ == '__main__':
    app.run(port=10000)
