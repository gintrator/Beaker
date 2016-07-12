class Beaker:

    """
    request and response objects are dictionaries.
    This class is responsible for casting all values to strings.
    method  -> REST Verb
    path    -> URI
    status  -> HTTP Status Code
    body    -> payload
    """

    def __init__(self, name='default'):
        self.name = name
        self.paths = {}
        self.content_types = {}

    def produces(self, content_type):
        def decorator(func):
            self.content_types[func.__name__] = content_type
            return func
        return decorator

    def register(self, path, method="GET", content_type='text/plain'):
        def decorator(func):
            self.paths[(path, method)] = func
            self.content_types[func.__name__] = content_type
            return func
        return decorator
    
    def get(self, path, content_type='text/plain'):
        return self.register(path, "GET", content_type)
    
    def post(self, path, content_type='text/plain'):
        return self.register(path, "POST", content_type)
    
    def delete(self, path, content_type='text/plain'):
        return self.register(path, "DELETE", content_type)

    def parse_req(self, req):
        path = req['path']
        method = req['method']
        args = {}
        if '?' in path:
            path, args = path.split('?')
            args = {k:v for (k,v) in (var.split('=') for var in args.split('&'))}
        return (method, path, args)

    def request(self, req, res):
        method, path, args = self.parse_req(req)
        print "Request: {0} {1}".format(method, path)
        if (path, method) not in self.paths:
            return False
        func = self.paths[(path, method)]
        res['content'] = self.content_types[func.__name__]
        #args = ('1', '6')
        #args = tuple(e[0](e[1]) for e in zip(func.func_defaults, args))
        #func(req, res, *args)
        func(req, res)
        return True


