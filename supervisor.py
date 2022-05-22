from flask import Flask, request, jsonify
import numpy as np
from Constants import *
from SupervisorUtils import *

app = Flask(__name__)

tree = dict()


@app.route("/tree", methods=['GET'])
def getTree():
    return jsonify(tree)


@app.route("/node/register", methods=['POST'])
def registerNode():
    node_ip, node_port = getRegisterNodeInfo(request.json)
    node_id = f'{node_ip}:{node_port}'
    if len(tree) == 0:
        tree[node_id] = {
            FATHER: None,
            SONS: []
        }
    else:
        print("in else")
    return "ok"


if __name__ == '__main__':
    app.run(port=10000)
