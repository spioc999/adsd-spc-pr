from cmd import Cmd
import socket
from threading import Thread

class myPrompt(Cmd):
    prompt = '>'
    intro  = 'Welcome on cmd client' 
   
    def __init__(self):
        super().__init__()
        self.socket = None
        self.is_connect = False

    def receive_messages(self, socket):
        while True:
            print("Waiting for messages")
            data = socket.recv(1024)
            if not data:
                print("disconnected")
                self.do_disconnect(None)
            else:
                print(f"[SUPERVISOR] {data.decode()}")


    def do_exit(self, inp):
        print('See you next time!')
        self.close()
        return True
    
    def do_connect(self, inp):
        if not self.is_connect:
            try:
                args = inp.split(' ')
                address = args[0]
                port = int(args[1])
                self.socket = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
                self.socket.connect((address, port))
                self.is_connect = True
                Thread(target=self.receive_messages, args=(self.socket,)).start()
                print(self.socket)
            except:
                print("Error during connection... try again")

    def do_disconnect(self, inp):
        if self.is_connect:
            self.socket.close()
            self.is_connect = False

    def do_sendMessage(self, inp):
        if self.is_connect:
            messaggio = inp
            self.socket.sendall(messaggio.encode('UTF-8'))

    # Chiudere tutte le risorse potenzialmente attive
    def close(self):
        if self.is_connect:
            self.socket.close()
        pass

if __name__ == '__main__':
    prompt = myPrompt()
    prompt.cmdloop()