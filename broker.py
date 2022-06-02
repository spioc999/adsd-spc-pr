import random
import socket
import sys
from threading import Thread
from utils.broker_utils import *
import os

port = None
host_address = None
pid = None


def connection_manager_thread(connection_id):
    """
    This service waits for messages from connection, after received the message manage it in order to communicate with brokers and clients
    :param connection_id: the connection which the broker is waiting for messages
    :return: None
    """
    print(f"Started connection manager for {connection_id}...")
    conn = get_connection_by_id(connection_id)
    connection_lost = False
    while not connection_lost:
        data = conn.recv(1024)
        if not data:
            should_reconnect = handle_active_connection_lost(connection_id, get_node_id(host_address, port))
            connection_lost = True
            if should_reconnect:
                connect_to_broker_network()
        else:
            try:
                command, value = get_command_and_value(data)
                if command == Command.PORT:
                    status_code = handle_command_port(value, connection_id, host_address, port)
                    if status_code != 200:
                        print(f"Closing connection with {connection_id}")
                        conn.close()
                        delete_active_connection(connection_id)
                        connection_lost = True
                        if status_code == 12163:
                            print(f"Status code = {status_code}. Reconnecting to network")
                            connect_to_broker_network()
                elif command == Command.USER:
                    handle_command_user(value, connection_id)
                elif command == Command.SUBSCRIBE:
                    handle_command_subscribe(value, connection_id)
                elif command == Command.UNSUBSCRIBE:
                    handle_command_unsubscribe(value, connection_id)
                elif command == Command.SEND:
                    handle_command_send(value, connection_id)
                else:
                    print(data.decode('UTF-8'))
            except Exception as e:
                print(e)
                conn.sendall(build_command(Command.RESULT, 'ERROR'))


def broker_tcp_server_manager():
    """
    This method create a tcp server and wait for connections.
    After each connection create a thread to manage it.
    :return: None
    """
    tcp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    try:
        tcp_server_socket.bind(('0.0.0.0', port))
    except OSError as osError:
        print("Received osError. QUIT")
        sys.exit()
    print('Broker UP (port: {} - PID: {})'.format(port, pid))
    try:
        while True:
            print('Waiting for connections ...')
            tcp_server_socket.listen()
            conn, address = tcp_server_socket.accept()
            print(f"Connection established with: {address}")
            conn.sendall(build_command(Command.RESULT, "OK"))
            connection_id = add_connection(address[0], address[1], conn)
            Thread(target=connection_manager_thread, args=(connection_id,), ).start()

    finally:
        if tcp_server_socket:
            tcp_server_socket.close()


def connect_to_broker_network(start_tcp_server=False):
    """
    This service connects the current broker to the network (thanks to supervisor) in order to communicate with other brokers
    :param start_tcp_server: variable that defines if this service must start a tcp server (for client connections) or not.
    :return: None
    """
    global port
    father_connection = None
    father_ip = None
    father_port = None

    while not father_connection or not father_ip or not father_port:
        status_code, father_ip, father_port, father_connection = register_current_node_and_connect_to_father()
        print(f"Received status code: {status_code}")
        if status_code == 409:  # Port out of range, changing port
            port = random.randint(LOWER_AVAILABLE_PORT, UPPER_AVAILABLE_PORT)  # if ip and port already in tree
            print(f"port changed to: {port}")

    if start_tcp_server:
        # start server tcp
        Thread(target=broker_tcp_server_manager).start()

    # adding father to active connections
    father_id = add_connection(father_ip, father_port, father_connection, is_broker=True, is_father=True)
    # start thread handling father broker connection
    Thread(target=connection_manager_thread, args=(father_id,)).start()


def register_current_node_and_connect_to_father():
    """
    This service asks the supervisor the father id and then tries to establish a tcp connection with the given father
    :return: response_status_code, father_ip, father_port, father_socket
    """
    response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/register', json={
        NODE_IP: host_address,
        NODE_PORT: port
    })
    if response.status_code != 200:
        print(response.text)
    else:
        try:
            ip_port_father = response.text.split(':')
            ip_father, port_father = ip_port_father[0], int(ip_port_father[1])
            father_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            father_socket.connect((ip_father, port_father))
            command, value = get_command_and_value(father_socket.recv(1024))
            if command == Command.RESULT and value == "OK":
                father_socket.sendall(build_command(Command.PORT, port))  # Sending broker tcp port. The supervisor must know the tcp port of each broker
                command, value = get_command_and_value(father_socket.recv(1024))
                if command == Command.RESULT and value == 'OK':
                    return response.status_code, ip_father, port_father, father_socket
        except Exception as exc:
            father_socket.close()
            print(f"Exception  in register: {exc}")
            if 'Connection refused' in exc.args[1]:
                print("Connection refused obtained")
                sys.exit()

    return response.status_code, None, None, None


if __name__ == '__main__':
    args = broker_initialize_parser()
    port = args.socket_port
    host_address = get_host_address()
    pid = os.getpid()  # get pid in order to kill arbitrary broker
    connect_to_broker_network(start_tcp_server=True)
