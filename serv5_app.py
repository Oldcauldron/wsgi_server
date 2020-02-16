from urls import urls
import re


def viewer(path=''):
    path_to_body = urls()

    for pattern in path_to_body:
        if re.match(pattern, path):
            return path_to_body[pattern]
    return False


class ResponseFormer():
    def __init__(self, env):
        self.env = env
        self.path = self.env['PATH_INFO']

    def test_method(self):
        if self.env['REQUEST_METHOD'] != 'GET':
            return self.fourzerofour()
        return self.try_body()

    def try_body(self):
        self.view = viewer(self.path)
        if self.view is False:
            return self.fourzerofour()
        path_to_file = 'pages'
        path_to_file += ''.join(self.view)
        status = '200 ok'
        with open(path_to_file, 'rb') as f:
            file = f.read()
            return status, file

    def fourzerofour(self):
        status = '404'
        file = b"None"
        return status, file


'''
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
'''


def app(environ, start_response):
    examp = ResponseFormer(environ)
    status, file = examp.test_method()
    start_response(status, response_headers=[])
    return iter([file])


