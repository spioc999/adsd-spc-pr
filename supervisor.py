import json

from flask import Flask, request, jsonify
from SupervisorUtils import *
from Node import Node

app = Flask(__name__)

tree = dict()


@app.route("/tree", methods=['GET'])
def getTree():
    outputTree = tree.copy()
    for node in outputTree:
        sonArray = []
        for son in outputTree[node][SONS]:
            sonArray.append(son.toJSON())
        outputTree[node][SONS] = sonArray
    return jsonify(outputTree)


@app.route("/node/register", methods=['POST'])
def registerNode():
    node_ip, node_port = getRegisterNodeInfo(request.json)
    node_id = f'{node_ip}:{node_port}'
    father_id = None
    if len(tree) == 0:
        tree[node_id] = {
            FATHER: None,
            SONS: []
        }
        return '', 200
    else:
        for node in tree:
            if len(tree[node][SONS]) < TREE_BRANCH_SIZE:
                father_id = node
                tree[node][SONS].append(Node(node_ip, node_port))
    return father_id, 200


if __name__ == '__main__':
    app.run(port=10000)
