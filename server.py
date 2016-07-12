import socket
import pprint
import time

HTTP_OK = 'HTTP/1.0 200 OK\r\n\r\n'
HTTP_NOT_FOUND = 'HTTP/1.0 404 NOT FOUND\r\n\r\n'
CRLF = '\r\n'

class Server:

    """
    Simple HTTP Server

    Named pygi - pronounced 'Piggy'

    Internal request and response objects are maintained as dictionaries.
    parse_request and create_response_str exists to marshall to and from these structures.
    """

    def __init__(self, port, app, host=''):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen(1)
        self.port = port
        self.app = app
        self.server_name = 'pygi'

    def serve(self):
        print "Serving at {0}:{1}. Waiting for requests.".format(socket.gethostname(), self.port)
        while True:
            connection_socket, address = self.server_socket.accept()
            data = connection_socket.recv(1024)
            req = self.parse_request(data)
            res = self.create_new_response()
            valid_request = self.app.request(req, res)
            if not valid_request:
                connection_socket.send(HTTP_NOT_FOUND)
            else:
                connection_socket.send(self.create_response_str(res))
            connection_socket.close()

    def create_new_response(self):
        res = {'status': 500,
               'body': '',
               'content': 'text/plain'}
        return res

    def create_response_str(self, res):
        """
        Turn this response dict into an HTTP response string.
        """
        headers = ["HTTP/1.0 200 OK",
                   "Server: {0}".format(self.server_name),
                   "Date: {0}".format(time.strftime('%a, %d %b %Y %H:%M:%S %Z')),
                   "Content-Type: {0}".format(res['content']),
                   "Content-Length: {0}".format(len(res['body']))]
        response = "{0}{1}{2}{3}".format(CRLF.join(headers), CRLF, CRLF, res['body'])
        return response

    def parse_request(self, request):
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
        parsed_request['body'] = request[body_i].strip()
        return parsed_request

