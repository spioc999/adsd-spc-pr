FATHER = "father"
SONS = "sons"
NODE_IP = "node_ip"
NODE_PORT = "node_port"
STATUS = "status"
TIME = "time"
TREE_BRANCH_SIZE = 2 #Binary tree
SON = "son"


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
