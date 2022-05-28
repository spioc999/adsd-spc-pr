import random
import socket
from threading import Thread
from utils.common_utils import *
from utils.broker_utils import *

port = None
host_address = None


def connection_manager_thread(connection_id):
    # What should be do here
    # 1. Wait for messages
    # 2. after a message received decode command and vaulue
    # and manage it in order to let broker communicate to each other
    #    2.1 Receive a message and redirect it to all connections except the this one active in this thread
    # 3. if connection is closed manage it as follow:
    # if client: do nothing
    # if a son node -> call the service supervisor.sonDown
    # if a father node -> call the service supervisor.fatherDown and then reconnecto to network #
    # (During this phase we should save messages received in order to
    # redirect them on the network when connection is esthabilished?)
    print(f"Started connection manager for {connection_id}...")
    conn = get_connection_by_id(connection_id)
    connection_lost = False
    while not connection_lost:
        data = conn.recv(1024)
        if not data:
            connection_lost, should_reconnect = \
                handle_active_connection_lost(connection_id, f'{host_address}:{port}')
            if should_reconnect:
                connect_to_broker_network()
        else:
            print(data.decode('UTF-8'))  # TODO


def broker_tcp_server_manager():
    """
    This method create a tcp server and wait for connections.
    After each connection create a thread to manage it.
    :return: None
    """
    tcp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcp_server_socket.bind(('0.0.0.0', port))
    print('Broker UP (port: {})'.format(port))
    try:
        while True:
            print('Waiting for connections ...')
            tcp_server_socket.listen()
            conn, address = tcp_server_socket.accept()
            connection_id = add_connection(address[0], address[1], conn)
            Thread(target=connection_manager_thread, args=(connection_id,), ).start()

    finally:
        if tcp_server_socket:
            tcp_server_socket.close()


def connect_to_broker_network(start_tcp_server=False):
    global port
    father_connection = None
    father_ip = None
    father_port = None

    while not father_connection or not father_ip or not father_port:
        status_code, father_ip, father_port, father_connection = register_current_node_and_connect_to_father()
        if status_code == 409:
            port = random.randint(LOWER_AVAILABLE_PORT, UPPER_AVAILABLE_PORT)  # if ip and port already in tree

    if start_tcp_server:
        # start server tcp
        Thread(target=broker_tcp_server_manager).start()

    # adding father to active connections
    father_id = add_connection(father_ip, father_port, father_connection, is_broker=True, is_father=True)
    # start thread handling father broker connection
    Thread(target=connection_manager_thread, args=(father_id,)).start()


def register_current_node_and_connect_to_father():
    response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/register', json={
        'node_ip': host_address,
        'node_port': port
    })
    if response.status_code != 200:
        print(response.text)
    else:
        try:
            ip_port_father = response.text.split(':')
            ip_father, port_father = ip_port_father[0], int(ip_port_father[1])
            father_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            father_socket.connect((ip_father, port_father))
            father_socket.sendall(build_command(Command.PORT, port))
            command, value = get_command_and_value(father_socket.recv(1024))
            if command == Command.RESULT and value == 'OK':
                return response.status_code, ip_father, port_father, father_socket
        except Exception as e:
            print(e)

    return response.status_code, None, None, None


if __name__ == '__main__':
    args = broker_initialize_parser()
    port = args.socket_port
    host_address = get_host_address()
    connect_to_broker_network(start_tcp_server=True)
