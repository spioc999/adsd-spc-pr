import argparse
from threading import Lock
from utils.constants import *
import requests
from utils.common_utils import *

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
        CONNECTION: connection,
        IS_BROKER: is_broker,
        IP: ip,
        PORT: port,
        IS_FATHER: is_father
    }
    mutexACs.release()
    return connection_id


def update_info_connection(connection_id, is_broker=None, port=None):
    mutexACs.acquire()
    if connection_id in activeConnections:
        if is_broker is not None:
            activeConnections[connection_id][IS_BROKER] = is_broker
        if port is not None:
            activeConnections[connection_id][PORT] = port
    mutexACs.release()


def get_connection_by_id(connection_id):
    mutexACs.acquire()
    conn = activeConnections[connection_id][CONNECTION]
    mutexACs.release()
    return conn


def delete_active_connection(connection_id):
    mutexACs.acquire()
    del activeConnections[connection_id]
    mutexACs.release()


def get_info_ac_by_id(connection_id):
    mutexACs.acquire()
    is_broker = activeConnections[connection_id][IS_BROKER]
    is_father = activeConnections[connection_id][IS_FATHER]
    ip = activeConnections[connection_id][IP]
    port = activeConnections[connection_id][PORT]
    mutexACs.release()
    return is_broker, is_father, ip, port


def handle_active_connection_lost(connection_id, current_node_id):
    """
    This method handles the connection lost case
    :param connection_id: connection lost id
    :param current_node_id: current node id
    :return: connection_lost, should_reconnect_network -> (boolean, boolean) tuple
    """
    is_broker, is_father, ip_down, port_down = get_info_ac_by_id(connection_id)
    if not is_broker:
        print(f'client connection lost: {connection_id}!')
        delete_active_connection(connection_id)
        return True, False

    # broker connection handling
    broker_down_id = f'{ip_down}:{port_down}'
    response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/down', json={
        'node_id': current_node_id,
        'down_id': broker_down_id
    })

    if not is_father:  # means that current broker is the father of lost node
        if response.status_code != 200:
            print(f'ERROR {response.status_code} communicating son broker down: {broker_down_id}')
        else:
            print(f'son broker down ({broker_down_id}) and communicated correctly to supervisor!')
            delete_active_connection(connection_id)
            return True, False
    else:
        if response.status_code != 200:
            print(f'ERROR {response.status_code} communicating father broker down: {broker_down_id}')
        else:
            print(f'father broker connection lost ({broker_down_id}) and communicated correctly to supervisor!')
            delete_active_connection(connection_id)
            return True, True

    # here only if error from service
    return False, False


def handle_command_port(port_value, connection_id, current_node_ip, current_node_port):
    conn = get_connection_by_id(connection_id)
    if port_value < LOWER_AVAILABLE_PORT or port_value > UPPER_AVAILABLE_PORT:
        conn.sendall(build_command(Command.RESULT, 'ERROR'))
        print(f"Error {port_value} not allowed as port value")
    else:
        ip_node = connection_id.split(':')[0]
        response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/confirm', json={
            'father': {
                'node_ip': current_node_ip,
                'node_port': current_node_port
            },
            'son': {
                'node_ip': ip_node,
                'node_port': port_value
            }
        })

        if response.status_code != 200:
            conn.sendall(build_command(Command.RESULT, 'ERROR'))
            print(f'Error during confirm broker {ip_node}:{port_value}!')
        else:
            update_info_connection(connection_id, is_broker=True, port=port_value)
            conn.sendall(build_command(Command.RESULT, 'OK'))
            print(f'Broker {ip_node}:{port_value} confirmed successfully!')
