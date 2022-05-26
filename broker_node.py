import socket
from threading import Thread, Lock
from utils.common_utils import *
from utils.broker_utils import *
import requests

SUPERVISOR_ENDPOINT = 'http://127.0.0.1:10000'
activeConnections = dict()
mutexACs = Lock()
mutexTOPICs = Lock()
topics = dict()


def connection_manager_thread(id_):
    pass


def broker_tcp_server_manager(server_port):
    global activeConnections
    global mutexACs
    global mutexTOPICs
    global topics
    tcp_server_socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
    tcp_server_socket.bind(('0.0.0.0', server_port))
    try:
        while True:
            print('Broker UP (port: {}), waiting for connections ...'.format(server_port))
            tcp_server_socket.listen()
            conn, address = tcp_server_socket.accept()

            connection_id = f'{address[0]}:{address[1]}'
            mutexACs.acquire()
            activeConnections[connection_id] = {
                'connection': conn,
                'is_broker': False,
                'ip': address[0],
                'port': address[1],
                'is_father': False
            }
            mutexACs.release()

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
    father_id = f'{father_ip}:{father_port}'
    mutexACs.acquire()
    activeConnections[father_id] = {
        'connection': father_connection,
        'is_broker': True,
        'ip': father_ip,
        'port': father_port,
        'is_father': True
    }
    mutexACs.release()

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
            message = f'[PORT] {tcp_port}'
            father_socket.sendall(message.encode('UTF-8'))
            response_from_father = father_socket.recv(1024)
            if 'OK' in response_from_father.decode():
                return ip_father, port_father, father_socket
        except Exception as e:
            print(e)

    return None, None, None


if __name__ == '__main__':
    args = broker_initialize_parser()
    port = args.socket_port
    host_address = get_host_address()
    connect_to_network_and_start_server(host_address, port)


