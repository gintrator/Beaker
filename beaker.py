import re
import collections

class DotDict(dict):
    def __getattr__(self, attr):
        return self.get(attr)
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delattr__

class Request(DotDict): pass
class Response(DotDict): pass

class Beaker:

    """
    Request object req will have:
    method  -> REST Verb
    path    -> URI
    version -> HTTP Version
    body    -> payload
    
    Response object res will have:
    body   -> payload
    status -> HTTP Status Code
    """

    VAR_KEY = ('var_key', )
    FUNC_KEY = ('func_key', )
    
    def __init__(self, name='default'):
        self.name = name
        self._routes = {}
        self._func_vars = collections.defaultdict(list)
    
    def get(self, path, mimetype='text/plain'):
        return self.register(path, "GET", mimetype)
    
    def post(self, path, mimetype='text/plain'):
        return self.register(path, "POST", mimetype)
    
    def delete(self, path, mimetype='text/plain'):
        return self.register(path, "DELETE", mimetype)
    
    def register(self, path, method="GET", mimetype='text/plain'):
        def decorator(func):
            self._add_to_routes(path, method, func, mimetype)
            return func
        return decorator

    def _add_to_routes(self, path, method, func, mimetype):
        paths = self._replace_path_vars(path, method, func)
        def add_routes(routes, paths):
            if len(paths) == 1:
                if paths[0] not in routes:
                    routes[paths[0]] = {}
                routes[paths[0]][(Beaker.FUNC_KEY, method)] = (func, mimetype)
                return routes[paths[0]]
            if paths[0] not in routes:
                routes[paths[0]] = {}
            return add_routes(routes[paths[0]], paths[1:])
        return add_routes(self._routes, paths)

    def _find_path_func(self, path, method):
        """
        Walks the route tree.
        Return the tuple (func, mimetype, path_taken) or (None, None, None)
        """
        paths = self._path_to_list(path)
        routes = self._routes
        path_taken = tuple()
        try:
            while len(paths) > 0:
                key = paths.pop(0)
                if key in routes:
                    routes = routes[key]
                    path_taken += (key, )
                elif Beaker.VAR_KEY in routes:
                    routes = routes[Beaker.VAR_KEY]
                    path_taken += Beaker.VAR_KEY
                else:
                    return (None, None, None)
            func, mimetype = routes[(Beaker.FUNC_KEY, method)]
            return (func, mimetype, path_taken)
        except KeyError as e:        
            return (None, None, None)

    def _replace_path_vars(self, path, method, func):
        """
        Populates the dictionary self._func_vars 
        Keys: func.__name__
        Values: Another dict with (var, value) mappings. value is '' for now.
        """
        paths = self._path_to_list(path)
        for i, path_part in enumerate(paths):
            var = self._check_var(path_part) 
            if var:
                paths[i] = Beaker.VAR_KEY
                self._func_vars[func.__name__].append(var)
        return paths

    def _check_var(self, path_part):
        match = re.search('<(.*)>', path_part)
        return match.group(1) if match else None

    def _path_to_list(self, path):
        return path.split('/')[1:]

    def _list_to_path(self, path_list):
        path_list = [''] + path_list
        return '/'.join(path_list)

    def _parse_request(self, req):
        path = req['path']
        method = req['method']
        args = {}
        if '?' in path:
            path, args = path.split('?')
            args = {k: v for (k, v) in (var.split('=') for var in args.split('&'))}
        return (method, path, args)

    def _get_kwargs(self, path, path_taken, func):
        path_list = self._path_to_list(path)
        func_vars = self._func_vars[func.__name__]
        kwargs = {k: v for (k, v) in zip(func_vars, filter(lambda e: e not in path_taken, path_list))}
        return kwargs

    def request(self, server_req, server_res):
        req = Request(server_req)
        method, path, args = self._parse_request(req)
        print "Request: {0} {1}".format(method, path)
        func, mimetype, path_taken = self._find_path_func(path, method)
        if not func:
            print "Not found: {0}".format(path)
            return False
        req.args = args
        kwargs = self._get_kwargs(path, path_taken, func)
        res = func(req, **kwargs)
        server_res['body'] = res.body
        server_res['status'] = res.status
        server_res['mimetype'] = mimetype
        return True

