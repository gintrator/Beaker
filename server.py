import socket
import time
import io

CRLF = '\r\n'

class Server:


    """
    Simple HTTP Server

    Named pygi - pronounced 'Piggy'

    Internal request and response objects are maintained as dictionaries.
    parse_request and create_response_str exists to marshall to and from these structures.
    """

    def __init__(self, port, app, host=''):
        self.port = port
        self.app = app
        self.host = host
        self.server_name = 'pygi'
        self.server_socket = self._create_server_socket()

    def _create_server_socket(self):
        """
        Create the main server socket.
        """
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(1)
        return server_socket

    def serve(self):
        """
        Server forever.
        """
        print "Serving at {0}:{1}. Waiting for requests.".format(socket.gethostname(), self.port)
        while True:
            connection_socket, address = self.server_socket.accept()
            data = connection_socket.recv(1024)
            req = self._parse_request(data)
            environ = self._create_environ(req)
            res_data = self.app(environ, self._start_response_on_socket(connection_socket))
            for res in res_data:
                connection_socket.send(res)
            connection_socket.close()

    def _start_response_on_socket(self, connection_socket):
        def start_response(status, headers):
            http_headers = ["HTTP/1.0 {0}".format(status),
                            "Server: {0}".format(self.server_name),
                            "Date: {0}".format(time.strftime('%a, %d %b %Y %H:%M:%S %Z'))]
            for (header, value) in headers:
                http_headers.append('{0}: {1}'.format(header, value))
            response = "{0}{1}{2}".format(CRLF.join(http_headers), CRLF, CRLF)
            connection_socket.send(response)
        return start_response

    def _parse_request(self, request):
        """
        Marshall a raw HTTP request into a dict.

        Returns dict with keys:
        method  -> str
        path    -> str
        version -> str
        headers -> dict
        body    -> str
        """
        parsed_request = {}
        request = request.split(CRLF)
        initial_line = request[0].split()
        parsed_request['method'] = initial_line[0]
        parsed_request['path'] = initial_line[1]
        parsed_request['version'] = initial_line[2]
        headers = {}
        body_i = 0
        for i in range(1, len(request)):
            if request[i] == '':
                body_i = i + 1
                break
            header, value = [e.strip() for e in request[i].split(':', 1)]
            headers[header] = value
        parsed_request['headers'] = headers
        body = request[body_i].strip()
        parsed_request['body'] = request[body_i].strip()
        return parsed_request


    def _create_environ(self, req):
        """
        Convert a request dict into a WSGI environ dict.
        """
        environ = {}
        args = ''
        path = req['path']
        if '?' in path:
            path, args = path.split('?')
        environ['PATH_INFO'] = path
        environ['QUERY_STRING'] = args
        environ['REQUEST_METHOD'] = req['method']
        if 'Content-Type' in req['headers']:
            environ['CONTENT_TYPE'] = req['headers']['Content-Type']
        if 'Content-Length' in req['headers']:
            environ['CONTENT_LENGTH'] = req['headers']['Content-Length']
        if 'Content-Type' in req['headers']:
            environ['CONTENT_TYPE'] = req['headers']['Content-Type']
        if 'body' in req:
            environ['wsgi.input'] = io.StringIO(u'{0}'.format(req['body']))
        return environ


