import socket
from threading import Thread
from utils.common_utils import *
from utils.broker_utils import *
import requests


def connection_manager_thread(connection_id):
    pass

def broker_tcp_server_manager(server_port):
    tcp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcp_server_socket.bind(('0.0.0.0', server_port))
    try:
        while True:
            print('Broker UP (port: {}), waiting for connections ...'.format(server_port))
            tcp_server_socket.listen()
            conn, address = tcp_server_socket.accept()
            connection_id = add_connection(address[0], address[1], conn)
            Thread(target=connection_manager_thread, args=(connection_id,), ).start()  #

    finally:
        if tcp_server_socket:
            tcp_server_socket.close()


def connect_to_network_and_start_server(ip, tcp_port):
    father_connection = None
    father_ip = None
    father_port = None

    while not father_connection or not father_ip or not father_port:
        father_ip, father_port, father_connection = register_node_and_connect_to_father(ip, tcp_port)

    # start server tcp
    Thread(target=broker_tcp_server_manager, args=(tcp_port,)).start()
    father_id = add_connection(father_ip, father_port, father_connection, is_broker=True, is_father=True)
    # start thread handling father broker connection
    Thread(target=connection_manager_thread, args=(father_id,)).start()


def register_node_and_connect_to_father(ip, tcp_port):
    response = requests.post(f'{SUPERVISOR_ENDPOINT}/node/register', json={
        'node_ip': ip,
        'node_port': tcp_port
    })
    if response.status_code != 200:
        print(response.text)
    else:
        try:
            ip_port_father = response.text.split(':')
            ip_father, port_father = ip_port_father[0], ip_port_father[1]
            father_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            father_socket.connect((ip_father, port_father))
            father_socket.sendall(build_command(Command.PORT, tcp_port))
            command, value = get_command_and_value(father_socket.recv(1024))
            if command == Command.RESULT and value == 'OK':
                return ip_father, port_father, father_socket
        except Exception as e:
            print(e)

    return None, None, None


if __name__ == '__main__':
    args = broker_initialize_parser()
    port = args.socket_port
    host_address = get_host_address()
    connect_to_network_and_start_server(host_address, port)


