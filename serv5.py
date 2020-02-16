# Tested with Python 3.7 (Win 7)
import io
import socket
import sys
from threading import Thread
from queue import Queue
from datetime import datetime


class ClientThreads(Thread):
    def __init__(self, client_queue, application, server_port, server_name, i):
        Thread.__init__(self)
        self.client_queue = client_queue
        self.application = application
        self.server_port = server_port
        self.server_name = server_name
        self.num = i

        # for creating an image that facilitates understanding work
        # of the program
        self.ph_st = '>' * 20
        self.ph_fin = '<' * 20

    def run(self):
        while True:
            connect = self.client_queue.get()
            self.handle_one_request(connect)
            self.client_queue.task_done()
            connect.close()

    def handle_one_request(self, connect):
        request_data = connect.recv(1024)
        self.request_data = request_data = request_data.decode('utf-8')
        if len(request_data) == 0:
            return None

        '''
        Print formatted request data like:
        >>>>>>>>>>>>>>>>>>>> Start thread - 0 >>>>>>>>>>>>>>>>>>>>

        request_data info - 778
        > client trd_0 > GET /tree HTTP/1.1
        > client trd_0 > Host: localhost:8888
        '''
        print(f'\n{self.ph_st} Start thread - {self.num} {self.ph_st}\n')
        print(f'request_data info - {len(request_data)}')
        print(''.join(
            f'> client trd_{self.num} > {line}\n'
            for line in request_data.splitlines()
        ))

        # получает только верхний заголовок GET /hello HTTP/1.1
        # и в self передает 3 переменные - метод запроса, путь и версию запроса
        self.parse_request(request_data)

        '''
        Construct environment dictionary using request data.
        in env мы словарем передаем to application все что
        хочет клиент, путь дальше сервера, data, все что надо
        вернуть клиенту потом в плане имени сервера и порта
        '''
        env = self.get_environ()

        # It's time to call our application callable and get
        # back a result that will become HTTP response body.
        # To application мы передаем path, headers и data
        # от клиента. В result мы получаем ответ на path,
        # отпределенной data, and heders, from application.
        # ПРичем status and headers we take from start_response.
        # Start_response на сервер отправляет headers_set[]
        # (создает self.headers_set)
        # Получается result это только чистая data, причем
        # result это итератор
        result = self.application(env, self.start_response)

        '''
        Construct a response and send it back to the client.        
        in finish_response мы загружаем все заголовки из headers_set
        соединяем это с data, кодируем в response_bytes и это уже
        отправляем
        '''
        self.finish_response(result, connect)

    def parse_request(self, text):
        request_line = text.splitlines()[0]
        request_line = request_line.rstrip('\r\n')
        # Break down the request line into components
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

    def get_environ(self):
        env = {}
        env['wsgi.version'] = (1, 0)
        env['wsgi.url_scheme'] = 'http'
        # self.request_data это данные пришедшие от клиента
        # (включая заголовки и data)
        # их мы тут загружаем в буфферную память и передаем
        # ссылку на нее to application
        env['wsgi.input'] = io.StringIO(self.request_data)
        env['wsgi.errors'] = sys.stderr
        env['wsgi.multithread'] = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once'] = False
        env['REQUEST_METHOD'] = self.request_method    # GET
        env['PATH_INFO'] = self.path              # /hello
        env['SERVER_NAME'] = self.server_name       # localhost
        env['SERVER_PORT'] = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers=[], exc_info=None):
        # Add necessary server headers
        tt = datetime.strftime(datetime.now(), "%a, %d %b %Y %H:%M:%S")
        server_headers = [
            ('Date', tt),
            ('Server', 'WSGIServer 1.0'),
        ]
        self.headers_set = [status, response_headers + server_headers]
        # To adhere to WSGI specification the start_response must return
        # a 'write' callable. We simplicity's sake we'll ignore that detail
        # for now.
        # return self.finish_response

    def finish_response(self, result, connect):
        '''
        in response мы загружаем все заголовки из headers_set
        соединяем это с data, кодируем в response_bytes и это уже
        отправляем
        '''
        try:
            status, response_headers = self.headers_set
            response = f'HTTP/1.1 {status}\r\n'
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')

            '''
            Print like:
            < server trd_0 < HTTP/1.1 404
            < server trd_0 < Date: Sun, 16 Feb 2020 13:57:26
            < server trd_0 < Server: WSGIServer 1.0
            < server trd_0 <
            < server trd_0 < None
            '''
            print(''.join(
                f'< server trd_{self.num} < {line}\n'
                for line in response.splitlines()
            ))

            response_bytes = response.encode()
            connect.sendall(response_bytes)
        finally:
            '''
            Print like:
            <<<<<<<<<<<<<<<<<<<< Finish thread- 1 <<<<<<<<<<<<<<<<<<<<
            '''
            print(f'{self.ph_fin} Finish thread- {self.num} {self.ph_fin}\n\n')

            connect.close()


class WSGIServer(object):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 4

    def __init__(self, server_address):
        # ClientThreads.__init__(self)
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []
        self.client_queue = Queue()

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket

        for i in range(self.request_queue_size):
            print(f'_______Initial thread {i}__________')
            thrd = ClientThreads(
                self.client_queue, self.application,
                self.server_port, self.server_name, i)
            thrd.setDaemon(True)
            thrd.start()

        while True:
            # New client connection
            self.client_connection, client_address = listen_socket.accept()
            # Handle one request and close the client connection. Then
            # loop over to wait for another client connection
            self.client_queue.put(self.client_connection)


SERVER_ADDRESS = (HOST, PORT) = '', 8888


def make_server(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.exit('Provide a WSGI application object as module:callable\
 (for example serv5_app:app)')
    print('You can use client_imitation.py or browser for testing')
    app_path = sys.argv[1]
    module, application = app_path.split(':')
    module = __import__(module)
    application = getattr(module, application)
    httpd = make_server(SERVER_ADDRESS, application)
    print(f'WSGIServer: Serving HTTP on port {PORT} ...\n')
    httpd.serve_forever()
