'''
Client imitation for testing  serv5.py
'''
import argparse
import socket
import threading
import queue


SERVER_ADDRESS = 'localhost', 8888
REQUEST = b"""\
GET /index.html HTTP/1.1
Host: localhost:8888

data data data data data
data datd data data data
"""


class CliThread(threading.Thread):
    def __init__(self, server_address, request, que):
        super().__init__()
        self.server_address = server_address
        self.request = request
        self.que = que

    def run(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.server_address)
        self.sock.sendall(self.request)
        self.recv = self.sock.recv(1024)
        self.que.put(self.recv)


def main(max_clients, max_conns, server_address, request, que,
         num_of_que):
    # открываем поток каждому клиенту, отправляем запрос REQUEST, в потоке
    # кладем ответ в очередь que и делаем отметку в очереди num_of_que о старте
    # num_of_que нужен для ожидания ответа сервера в очередь que
    for client_num in range(max_clients):
        print(f'Client №{client_num} called')
        client_thread = CliThread(
            server_address, request, que)
        client_thread.setDaemon(True)
        client_thread.start()
        num_of_que.put(f'Thread №{client_num} started')


def execute_queue(que, num_of_que):
    try:
        while True:
            num_of_que.get(False)  # if(False), when queue empty raise exeption

            x = que.get(timeout=4)
            # if it have not exeption from num_of_que - wait x

            print(f'QUE - {x}')
            que.task_done()
            num_of_que.task_done()
    except queue.Empty:
        print('DONE')


def argunent_controller():
    parser = argparse.ArgumentParser(
        description='Test client for WSGI server.',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        '--max-conns',
        type=int,
        default=1024,
        help='Maximum number of connections per client.'
    )
    parser.add_argument(
        '--max-clients',
        type=int,
        default=14,
        help='Maximum number of clients.'
    )
    args = parser.parse_args()
    return args


if __name__ == '__main__':

    args = argunent_controller()

    que = queue.Queue()
    num_of_que = queue.Queue()

    main(args.max_clients, args.max_conns, SERVER_ADDRESS, REQUEST, que,
         num_of_que)

    execute_queue(que, num_of_que)
