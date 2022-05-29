import time

import broker_node
from cmd import Cmd
from threading import Thread


class myPrompt(Cmd):

    def __init__(self, broker_number, threads):
        super().__init__()
        self.threads = threads

    def do_start_broker(self):
        self.threads.append(Thread(target=starter, args=(len(self.threads),)))
        self.threads[len(self.threads)-1].start()

    def do_kill(self):
        thread_id = int(input("Which broker do you want to kill?\n"))
        if thread_id < len(self.threads):
            self.threads[thread_id].kill()


def starter(thread_id):
    print(f"Broker thread id: {thread_id}")
    broker_node.start()


if __name__ == "__main__":
    broker_number = int(input("How many brokers do you want to start?\n"))
    threads = []
    for _ in range(broker_number):
        threads.append(Thread(target=starter, args=(len(threads),)))
        threads[len(threads)-1].start()
        time.sleep(1)
    # prompt = myPrompt(int(broker_number))
    # prompt.cmdloop()