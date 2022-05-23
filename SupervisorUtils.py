FATHER = "father"
SONS = "sons"
NODE_IP = "node_ip"
NODE_PORT = "node_port"
TREE_BRANCH_SIZE = 2 #Binary tree


def getRegisterNodeInfo(json):
    if all(key in json.keys() for key in [NODE_IP, NODE_PORT]):

        return json[NODE_IP], json[NODE_PORT]
    else:
        print("Throws exception")
