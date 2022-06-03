from cmd import Cmd
import socket
from threading import Thread
import requests

from utils.common_utils import *
from utils.constants import *

SUPERVISOR_ENDPOINT = 'http://127.0.0.1:10000'


def _build_json(key, value):
    return json.dumps({
        key: value
    })


def _build_double_json(key1, value1, key2, value2):
    return json.dumps({
        key1: value1,
        key2: value2
    })


class ClientTcpCmd(Cmd):
    prompt = '>'
    intro = '\n\nWelcome on client. Make sure SUPERVISOR is up!\n' \
            'To start connection invoke - connect\n' \
            'Documentation is available typing <help>\n\n'

    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_connect = False
        self.topics = []
        self.listening_thread = None

    def do_connect(self, inp):
        """
        No input needed.
        This command get the first available broker and try to connect to it
        """
        if self.is_connect:
            print("Already connected.")
            return
        response = requests.get(f'{SUPERVISOR_ENDPOINT}/broker')
        if response.status_code != 200:
            print(response.text)
        else:
            try:
                print(f"[INFO] -> Trying to connect to: {response.text}")
                split_text = response.text.split(':')
                address = split_text[0]
                port = int(split_text[1])
                self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                self.socket.connect((address, port))
                self.is_connect = True
                print(f'[CONNECTED] -> Broker: {response.text}\n')
                self.listening_thread = Thread(target=self._receive_messages, args=(self.socket,)).start()
            except Exception as e:
                self.socket = None
                self.is_connect = False
                self.topics = []
                print(f'[ERROR] -> Connection failed: {e}')

    def do_exit(self, inp):
        """
        No input needed.
        Disconnect from broker and close console
        """
        self.do_disconnect(None)
        print('See you next time!')
        self._close()
        return True

    def do_disconnect(self, inp):
        """
        No input needed.
        Disconnect from broker.
        """
        if self.is_connect and self.socket:
            print("[INFO] -> closing tcp connection")
            self.socket.close()
            self.is_connect = False
            self.topics = []
            print("[INFO] All done. Ready for new connections.")

    def do_username(self, username):
        """
        Set a username that will be used to identify message sender
        :param username -> your username
        """
        if username:
            self._send_message_to_socket_safely(build_command(Command.USER, _build_json(USERNAME, username)))

    def do_send(self, inp):
        """
        No input needed.
        Type the send command and follow screen instructions
        """
        if len(self.topics) == 0:
            print("No topics available")
            return
        print("\n\nAvailable topics: ")
        self.do_topics(None)
        topic = None
        while topic not in self.topics:
            topic = input("\nIn which topic do you want to send the message?\n")
            if not topic in self.topics:
                print("Invalid topic. Retry!\n")
        message = input("Message: ")
        if message and topic:
            self._send_message_to_socket_safely(build_command(Command.SEND, _build_double_json(MESSAGE, message, TOPIC, topic)))
        else:
            print("Invalid info. Retry")

    def do_subscribe(self, topic):
        """
        Subscribe current user to specified topic
        :param: topic -> Topic name
        """
        if topic:
            self._send_message_to_socket_safely(build_command(Command.SUBSCRIBE, _build_json(TOPIC, topic)), topic=topic)

    def do_unsubscribe(self, topic):
        """
        Unsubscribe from specified topic
        :param: topic -> topic name
        """
        if topic:
            if topic in self.topics:
                self.topics.remove(topic)
            self._send_message_to_socket_safely(build_command(Command.UNSUBSCRIBE, _build_json(TOPIC, topic)))

    def do_topics(self, inp):
        """
        No input needed.
        Return the list of subscribed topics
        """
        if len(self.topics) == 0:
            print("No topics available")
            return
        for topic in self.topics:
            print(topic)

    # UTILS METHODS
    def _close(self):
        if self.is_connect and self.socket:
            self.socket.close()

    def _receive_messages(self, conn):
        while self.is_connect:
            try:
                data = conn.recv(1024)
                if not data:
                    print("Connection lost with broker!")
                    self.do_disconnect(None)
                else:
                    print(f"[BROKER] {data.decode('UTF-8')}\n")
            except Exception as e:
                if e.args[0] == 9:
                    self.is_connect = False
                    self.topics = []
                else:
                    print(f"[ERROR] -> Listening on messages\nException: {e}")

    def _send_message_to_socket_safely(self, message, topic=None):
        try:
            if self.is_connect:
                self.socket.sendall(message)
                if topic:
                    self.topics.append(topic)
            else:
                print(f'[ERROR] -> client not connected yet. Invoke "get_broker_and_connect" before!')
        except Exception as e:
            print(f'[ERROR] -> error sending {message} !\nException: {e}')


if __name__ == '__main__':
    prompt = ClientTcpCmd()
    prompt.cmdloop()
