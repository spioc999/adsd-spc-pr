import argparse
from threading import Lock
from common_utils import *

mutexACs = Lock()
activeConnections = dict()
SUPERVISOR_ENDPOINT = 'http://127.0.0.1:10000'
mutexTOPICs = Lock()
topics = dict()


def broker_initialize_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument("-sp", "--socket_port",
                        help="Port number that will be assigned to broker's server socket",
                        required=False,
                        type=int,
                        default=UPPER_AVAILABLE_PORT)
    return parser.parse_args()


def add_connection(ip, port, connection, is_broker=False, is_father=False):
    """
    This method add the given connection to the list of active connections
    :param ip: connection ip
    :param port: connection port -> if broker this represents its tcp server port
    :param connection: tcp connection
    :param is_broker:
    :param is_father: tell us if it's a father node
    :return:
    """
    connection_id = f'{ip}:{port}'
    mutexACs.acquire()
    activeConnections[connection_id] = {
        'connection': connection,
        'is_broker': is_broker,
        'ip': ip,
        'port': port,
        'is_father': is_father
    }
    mutexACs.release()
    return connection_id
