class Beaker:

    def __init__(self, name='default'):
        self.name = name
        self.paths = {}
        self.content_types = {}

    def produces(self, content_type):
        def decorator(func):
            self.content_types[func.__name__] = content_type
            return func
        return decorator

    def register(self, path, method):
        def decorator(func):
            self.paths[(path, method)] = func
            self.content_types[func.__name__] = 'text/plain'
            return func
        return decorator

    def request(self, req, res):
        """
        res will be a fully formed response dict, but with known Content  info.
        It only requires these to be put into the dict.
        """
        path = req['path']
        method = req['method']
        if (path, method) not in self.paths:
            return False
        func = self.paths[(path, method)]
        content_type = self.content_types[func.__name__]
        payload = func()
        res['body'] = payload
        res['headers']['Content-Type'] = content_type
        res['headers']['Content-Length'] = str(len(payload))
        return True

