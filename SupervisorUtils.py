from Constants import *



def getRegisterNodeInfo(json):
    if all(key in json.keys() for key in [NODE_IP, NODE_PORT]):

        return json[NODE_IP], json[NODE_PORT]
    else:
        print("Throws exception")
