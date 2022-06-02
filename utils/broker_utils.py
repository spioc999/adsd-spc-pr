import argparse
import copy
from threading import Lock
from utils.constants import *
import requests
from utils.common_utils import *
from enums.MessageResponseType import MessageResponseType

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


def add_connection(ip, port, connection, is_broker=False, is_father=False, username=None):
    """
    This method add the given connection to the list of active connections
    :param ip: connection ip
    :param port: connection port -> if broker this represents its tcp server port
    :param connection: tcp connection
    :param is_broker:
    :param is_father: tell us if it's a father node
    :param username: username of connection
    :return: None
    """
    connection_id = f'{ip}:{port}'
    mutexACs.acquire()
    activeConnections[connection_id] = {
        CONNECTION: connection,
        IS_BROKER: is_broker,
        IP: ip,
        PORT: port,
        IS_FATHER: is_father,
        USERNAME: username
    }
    mutexACs.release()
    return connection_id


def update_info_connection(connection_id, is_broker=None, port=None, username=None):
    mutexACs.acquire()
    if connection_id in activeConnections:
        if is_broker is not None:
            activeConnections[connection_id][IS_BROKER] = is_broker
        if port is not None:
            activeConnections[connection_id][PORT] = port
        if username is not None:
            activeConnections[connection_id][USERNAME] = username
    mutexACs.release()


def get_connection_by_id(connection_id):
    mutexACs.acquire()
    conn = activeConnections[connection_id][CONNECTION]
    mutexACs.release()
    return conn


def get_connection_username_and_is_broker_by_id(connection_id):
    mutexACs.acquire()
    conn = activeConnections[connection_id][CONNECTION]
    username = activeConnections[connection_id][USERNAME]
    is_broker = activeConnections[connection_id][IS_BROKER]
    mutexACs.release()
    return conn, username, is_broker


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
    username = activeConnections[connection_id][USERNAME]
    mutexACs.release()
    return is_broker, is_father, ip, port, username


def add_subscription(connection_id, topic):
    global topics
    global mutexTOPICs
    mutexTOPICs.acquire()
    if topic not in topics:
        topics[topic] = set()
    topics[topic].add(connection_id)
    mutexTOPICs.release()


def remove_subscritions(connection_id):
    global topics
    global mutexTOPICs
    mutexTOPICs.acquire()
    for topic in topics:
        if connection_id in topics[topic]:
            topics[topic].remove(connection_id)
            print(f"{connection_id} removed from topic: {topic}")
        else:
            print(f"{connection_id} not in topic: {topic}")
    mutexTOPICs.release()


def remove_subscription(connection_id, topic):
    global topics
    global mutexTOPICs
    mutexTOPICs.acquire()
    if connection_id in topics[topic]:
        topics[topic].remove(connection_id)
        print(f"{connection_id} removed from topic: {topic}")
        if len(topics[topic]) == 0:
            del topics[topic]
    else:
        print(f"{connection_id} not in topic: {topic}")
    mutexTOPICs.release()


def send_message(connection_id, message, topic, timestamp, username):
    """
    This method get all connections that should receive this message.
    Send message as it is to clients and add the [SEND] command to other brokers
    """
    global topics
    global mutexTOPICs
    global activeConnections
    global mutexACs

    mutexTOPICs.acquire()
    connections_to_send = set()
    if topic in topics:
        connections_to_send = copy.deepcopy(topics[topic])
    mutexTOPICs.release()

    mutexACs.acquire()
    brokers_connections = {k for k in activeConnections if activeConnections[k][IS_BROKER]}
    connections_to_send.update(brokers_connections)
    connections_to_send.remove(connection_id)

    for c in connections_to_send:
        conn = activeConnections[c][CONNECTION]
        is_broker = activeConnections[c][IS_BROKER]
        message_json = create_socket_message(message_type=MessageResponseType.NEW_MESSAGE, message=message,
                                             topic=topic, timestamp=timestamp, username=username, encode=False)
        if is_broker:
            conn.sendall(build_command(Command.SEND, message_json))  # Broker need a command to redirect the message
        else:
            conn.sendall(message_json.encode('UTF-8'))

    mutexACs.release()


def handle_active_connection_lost(connection_id, current_node_id):
    """
    This method handles the connection lost case
    :param connection_id: connection lost id
    :param current_node_id: current node id
    :return: connection_lost, should_reconnect_network -> (boolean, boolean) tuple
    """
    is_broker, is_father, ip_down, port_down, _ = get_info_ac_by_id(connection_id)
    if not is_broker:
        print(f'client connection lost: {connection_id}!')
        delete_active_connection(connection_id)
        remove_subscritions(connection_id)
        return False

    # broker connection handling
    broker_down_id = get_node_id(ip_down, port_down)
    response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/down', json={
        NODE_ID: current_node_id,
        DOWN_ID: broker_down_id
    })

    if not is_father:  # means that current broker is the father of lost node
        if response.status_code != 200:
            print(f'ERROR {response.status_code} communicating son broker down: {broker_down_id}')
        else:
            print(f'son broker down ({broker_down_id}) and communicated correctly to supervisor!')
    else:
        if response.status_code != 200:
            print(f'ERROR {response.status_code} communicating father broker down: {broker_down_id}')
        else:
            print(f'father broker connection lost ({broker_down_id}) and communicated correctly to supervisor!')
    delete_active_connection(connection_id)
    return is_father


def handle_command_port(port_value, connection_id, current_node_ip, current_node_port):
    """
    This method manage the [PORT] command received in tcp connection
    """
    conn = get_connection_by_id(connection_id)
    if port_value < LOWER_AVAILABLE_PORT or port_value > UPPER_AVAILABLE_PORT:
        conn.sendall(build_command(Command.RESULT, 'ERROR'))
        print(f"Error {port_value} not allowed as port value")
    else:
        ip_node = connection_id.split(':')[0]
        response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/confirm', json={
            FATHER: {
                NODE_IP: current_node_ip,
                NODE_PORT: current_node_port
            },
            SON: {
                NODE_IP: ip_node,
                NODE_PORT: port_value
            }
        })

        if response.status_code != 200:
            conn.sendall(build_command(Command.RESULT, 'ERROR'))
            print(f'I\'m {get_node_id(current_node_ip, current_node_port)} Error during confirm broker {get_node_id(ip_node,port_value)}!')
        else:
            update_info_connection(connection_id, is_broker=True, port=port_value)
            conn.sendall(build_command(Command.RESULT, 'OK'))
            print(f'Broker {get_node_id(ip_node,port_value)} confirmed successfully!')
        return response.status_code


def create_socket_message(message_type, uuid=None, message=None, username=None, timestamp=None, topic=None,
                          encode=True):
    """
    This method create the message that should be sent as json based on given parameters
    """
    dict_to_send = dict()
    dict_to_send[TYPE] = message_type.name
    if message:
        dict_to_send[MESSAGE] = message
    if uuid:
        dict_to_send[UUID] = uuid
    if username:
        dict_to_send[USERNAME] = username
    if timestamp:
        dict_to_send[TIMESTAMP] = timestamp
    if topic:
        dict_to_send[TOPIC] = topic
    json_string = json.dumps(dict_to_send)
    if encode:
        return json_string.encode('UTF-8')
    return json_string


def handle_command_user(username_dict, connection_id):
    """
    This method manage the [USER] command received in tcp connection
    """
    conn = get_connection_by_id(connection_id)
    uuid_message = None
    if UUID in username_dict:
        uuid_message = username_dict[UUID]

    if USERNAME in username_dict:
        username = username_dict[USERNAME]
        update_info_connection(connection_id, username=username)
        conn.sendall(create_socket_message(MessageResponseType.OK_USER, uuid_message,
                                           message=f'{username} as username inserted!'))
    else:
        conn.sendall(create_socket_message(MessageResponseType.ERROR_USER, uuid_message, message='username missing'))


def handle_command_subscribe(subscribe_dict, connection_id):
    """
    This method manage the [SUBSCRIBE] command received in tcp connection
    """
    conn = get_connection_by_id(connection_id)
    uuid_message = None
    if UUID in subscribe_dict:
        uuid_message = subscribe_dict[UUID]

    if TOPIC in subscribe_dict:
        topic = subscribe_dict[TOPIC]
        add_subscription(connection_id, subscribe_dict[TOPIC])
        conn.sendall(create_socket_message(MessageResponseType.OK_SUBSCRIBE, uuid_message,
                                           message=f'Subscribed to topic: {topic}!'))
    else:
        conn.sendall(create_socket_message(MessageResponseType.ERROR_SUBSCRIBE, uuid_message, message='topic missing'))


def handle_command_unsubscribe(unsubscribe_dict, connection_id):
    """
    This method manage the [UNSUBSCRIBE] command received in tcp connection
    """
    conn = get_connection_by_id(connection_id)
    uuid_message = None
    if UUID in unsubscribe_dict:
        uuid_message = unsubscribe_dict[UUID]

    if TOPIC in unsubscribe_dict:
        topic = unsubscribe_dict[TOPIC]
        remove_subscription(connection_id, topic)
        conn.sendall(create_socket_message(MessageResponseType.OK_UNSUBSCRIBE, uuid_message,
                                           message=f'Unsubscribed to topic: {topic}!'))
    else:
        conn.sendall(create_socket_message(MessageResponseType.ERROR_UNSUBSCRIBE, uuid_message,
                                           message='topic missing'))


def handle_command_send(send_dict, connection_id):
    """
    This method manage the [SEND] command received in tcp connection
    """
    conn, username, is_broker = get_connection_username_and_is_broker_by_id(connection_id)
    uuid_message = None
    if UUID in send_dict:
        uuid_message = send_dict[UUID]

    if TOPIC in send_dict and MESSAGE in send_dict:
        message = send_dict[MESSAGE]
        topic = send_dict[TOPIC]
        if not is_broker:
            if topic not in topics:
                conn.sendall(create_socket_message(MessageResponseType.ERROR_SEND,
                                                   uuid_message, message=f'Topic ({topic}) invalid!'))
                return
            elif connection_id not in topics[topic]:
                conn.sendall(create_socket_message(MessageResponseType.ERROR_SEND,
                                                   uuid_message, message=f'Not subscribed to {topic}!'))
                return

        timestamp = None
        if TIMESTAMP in send_dict:
            timestamp = send_dict[TIMESTAMP]

        if USERNAME in send_dict:
            username = send_dict[USERNAME]

        send_message(connection_id, message, topic, timestamp, username)
        if not is_broker:
            conn.sendall(create_socket_message(MessageResponseType.OK_SEND, uuid_message,
                                               message=f'\"{message}\" sent to topic:{topic}!'))
        else:
            conn.sendall(build_command(Command.RESULT, 'OK message forwarded'))
    else:
        conn.sendall(create_socket_message(MessageResponseType.ERROR_SEND,
                                           uuid_message, message='topic and message mandatory!'))
