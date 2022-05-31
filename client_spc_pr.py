from cmd import Cmd
import socket
from threading import Thread
import requests
from utils.common_utils import *

SUPERVISOR_ENDPOINT = 'http://127.0.0.1:10000'


class ClientSpcPr(Cmd):
    prompt = '>'
    intro = 'Welcome on client. Make sure SUPERVISOR is up!\nTo start connection invoke "get_broker_and_connect"...'

    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_connect = False

    def do_get_broker_and_connect(self, inp):
        response = requests.get(f'{SUPERVISOR_ENDPOINT}/broker')
        if response.status_code != 200:
            print(response.text)
        else:
            try:
                split_text = response.text.split(':')
                address = split_text[0]
                port = int(split_text[1])
                self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                self.socket.connect((address, port))
                self.is_connect = True
                print(f'[CONNECTED] -> Broker: {response.text}')
                Thread(target=self._receive_messages, args=(self.socket,)).start()
            except Exception as e:
                self.socket = None
                self.is_connect = False
                print(f'[ERROR] -> Connection failed: {e}')

    def do_exit(self, inp):
        print('See you next time!')
        self._close()
        return True

    def _close(self):
        if self.is_connect and self.socket:
            self.socket.close()

    def do_disconnect(self, inp):
        if self.is_connect and self.socket:
            self.socket.close()
            self.is_connect = False

    def _receive_messages(self, conn):
        while self.is_connect:
            try:
                data = conn.recv(1024)
                if not data:
                    print("Connection lost with broker!")
                    self.do_disconnect(None)
                else:
                    print(f"[BROKER] {data.decode('UTF-8')}")
            except Exception as e:
                print(f"[ERROR] -> Listening on messages\nException: {e}")
                self.is_connect = False

    def _send_message_to_socket_safely(self, message):
        try:
            if self.is_connect:
                self.socket.sendall(message)
            else:
                print(f'[ERROR] -> client not connected yet. Invoke "get_broker_and_connect" before!')
        except Exception as e:
            print(f'[ERROR] -> error sending {message} !\nException: {e}')

    def do_set_username(self, inp):
        if inp:
            self._send_message_to_socket_safely(build_command(Command.USER, inp))

    def do_send_message(self, inp):
        if inp:
            self._send_message_to_socket_safely(build_command(Command.SEND, inp))

    def do_subscribe(self, inp):
        if inp:
            self._send_message_to_socket_safely(build_command(Command.SUBSCRIBE, inp))

    def do_unsubscribe(self, inp):
        if inp:
            self._send_message_to_socket_safely(build_command(Command.UNSUBSCRIBE, inp))


if __name__ == '__main__':
    prompt = ClientSpcPr()
    prompt.cmdloop()
